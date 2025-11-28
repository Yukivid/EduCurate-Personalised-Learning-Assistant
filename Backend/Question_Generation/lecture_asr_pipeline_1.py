import os
import yt_dlp
import whisperx
import torch
import ffmpeg
from datetime import datetime, timedelta
import google.generativeai as genai
import uuid
from dotenv import load_dotenv

load_dotenv() 

# ---------- CONFIG ----------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
AUDIO_FILE = "audio.wav"
VIDEO_URL = "https://www.youtube.com/watch?v=zfiSAzpy9NM&t=1s"   # change this
MODEL_SIZE = "small"  # smaller model → faster (options: tiny, base, small, medium)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # <--- put your Gemini API key here
# ----------------------------


def download_audio(url, out_path=AUDIO_FILE):
    """Download YouTube audio and convert to 16 kHz WAV."""
    print(f"[1/4] Downloading from YouTube: {url}")
    unique_id = uuid.uuid4().hex[:6]
    ydl_opts = {"format": "bestaudio/best", "outtmpl": f"temp_{unique_id}.%(ext)s", "quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print("[2/4] Extracting audio...")
    ffmpeg.input(f"temp_{unique_id}.webm").output(out_path, ac=1, ar=16000, vn=None).overwrite_output().run(quiet=True)
    if os.path.exists(f"temp_{unique_id}.webm"):
        os.remove(f"temp_{unique_id}.webm")

    print(f"✅ Audio saved as {out_path}")
    return out_path


def transcribe_audio(audio_path):
    """Transcribe using WhisperX (fast + accurate)."""
    print("[3/4] Loading WhisperX model...")
    model = whisperx.load_model(MODEL_SIZE, device=DEVICE, compute_type="float32")

    print("[4/4] Transcribing...")
    result = model.transcribe(audio_path)
    print(f"✅ Transcription complete. {len(result['segments'])} segments detected.")
    return result


def save_transcript(result, out_file="transcript.txt"):
    """Save transcript with timestamps."""
    print(f"💾 Saving transcript to {out_file}")
    with open(out_file, "w", encoding="utf-8") as f:
        for seg in result["segments"]:
            start_time = str(timedelta(seconds=int(seg["start"])))
            text = seg["text"].strip()
            f.write(f"[{start_time}] {text}\n")
    print("✅ Transcript saved successfully.")
    return out_file


def generate_bloom_questions(transcript_path):
    """Send transcript text to Gemini for Bloom question generation."""
    if not GEMINI_API_KEY.strip():
        print("⚠️ Gemini API key not set. Skipping question generation.")
        return

    print("🤖 Generating Bloom questions via Gemini...")
    import google.generativeai as genai

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        with open(transcript_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Keep transcript short to avoid token limit
        text = text[:15000]

        prompt = f"""
Generate exactly 5 Bloom's Taxonomy questions (Remembering → Creating)
based on this lecture transcript:

{text}

Each question must be labeled with its Bloom's level:
1. (Remembering)
2. (Understanding)
3. (Applying)
4. (Analyzing)
5. (Creating)
"""

        # ✅ Use the latest model name
        model = genai.GenerativeModel("models/gemini-2.5-pro")
        response = model.generate_content(prompt)

        # Ensure valid text output
        if not hasattr(response, "text") or not response.text:
            print("⚠️ No valid response text received from Gemini.")
            return

        output_text = response.text.strip()

        # Save to file
        with open("bloom_questions.txt", "w", encoding="utf-8") as f:
            f.write(output_text)

        print("\n✅ Bloom questions generated successfully → bloom_questions.txt")
        print("------------------------------------------------------------")
        print(output_text)
        print("------------------------------------------------------------")

    except Exception as e:
        print(f"❌ Error generating questions: {e}")


def process_video(url):
    """Full ASR + Bloom Question Generation pipeline (no diarization)."""
    start_time = datetime.now()
    print("🚀 Starting pipeline...\n")

    audio = download_audio(url)
    result = transcribe_audio(audio)
    transcript_file = save_transcript(result)
    generate_bloom_questions(transcript_file)

    total_time = (datetime.now() - start_time).seconds
    print(f"\n🎉 All steps done in {total_time} seconds!")


if __name__ == "__main__":
    process_video(VIDEO_URL)
