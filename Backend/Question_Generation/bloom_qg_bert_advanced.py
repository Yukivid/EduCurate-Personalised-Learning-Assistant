"""
Bloom-Level Question Generator (Unique + Stable Version)
--------------------------------------------------------
Generates unique Bloom’s Taxonomy questions (2 per level)
using the open-access model 'valhalla/t5-base-qg-hl'.
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import textwrap
from difflib import SequenceMatcher

# ---------- CONFIG ----------
TRANSCRIPT_PATH = "transcript.txt"
OUTPUT_FILE = "bloom_questions_unique.txt"
MODEL_NAME = "valhalla/t5-base-qg-hl"
NUM_QUESTIONS_PER_LEVEL = 2
SIMILARITY_THRESHOLD = 0.75  # fuzzy match threshold to avoid duplicates
# -----------------------------


def load_text(file_path):
    """Load and clean transcript text."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    return text.replace("\n", " ").replace("  ", " ")


def chunk_text(text, max_words=180):
    """Split long text into smaller chunks for stable generation."""
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


def is_similar(q1, q2, threshold=SIMILARITY_THRESHOLD):
    """Check if two questions are similar (ignoring punctuation/case)."""
    q1, q2 = q1.lower().strip("?!. "), q2.lower().strip("?!. ")
    return SequenceMatcher(None, q1, q2).ratio() > threshold


def generate_questions(model, tokenizer, text, bloom_level, num_questions, global_memory):
    """Generate Bloom-level questions using robust decoding and deduplication."""
    local_qs = []
    for chunk in chunk_text(text):
        prompt = f"Generate {num_questions} {bloom_level.lower()} questions from this text: {chunk}"
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                num_return_sequences=num_questions,
                num_beams=5,
                temperature=0.8,
                top_p=0.9,
                do_sample=True,
                repetition_penalty=2.0,
                max_length=80
            )

        decoded = [tokenizer.decode(o, skip_special_tokens=True).strip() for o in outputs]

        for q in decoded:
            if len(q.split()) < 5 or len(q.split()) > 25:
                continue
            # Ensure uniqueness (local + global)
            if any(is_similar(q, prev) for prev in set(local_qs).union(global_memory)):
                continue
            local_qs.append(q)
            global_memory.add(q)

        if len(local_qs) >= num_questions:
            break

    return list(local_qs)[:num_questions]


def main():
    print("📘 Reading transcript...")
    text = load_text(TRANSCRIPT_PATH)

    print("🤖 Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    bloom_levels = [
        "Remembering: recall key facts and definitions",
        "Understanding: explain ideas or summarize concepts",
        "Applying: use knowledge in new situations",
        "Analyzing: identify relationships or patterns",
        "Evaluating: make judgments based on criteria",
        "Creating: generate new ideas or propose solutions"
    ]

    print("\n🧠 Generating unique Bloom-level questions...\n")

    global_memory = set()  # ensure no repeated questions globally
    all_output = []

    for level in bloom_levels:
        questions = generate_questions(model, tokenizer, text, level, NUM_QUESTIONS_PER_LEVEL, global_memory)
        section = f"\n🟢 {level}\n"
        for i, q in enumerate(questions, 1):
            section += f"Q{i}: {q}\n"
        all_output.append(section)

    final_text = "\n".join(all_output)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_text)

    print(f"\n✅ Unique Bloom-level questions saved → {OUTPUT_FILE}")
    print("\n---- Preview ----")
    print(textwrap.shorten(final_text, width=1000, placeholder="..."))


if __name__ == "__main__":
    main()
