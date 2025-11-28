# transcript_clean.py
"""
Fetch and clean subtitles into a readable transcript.

Features:
- YouTube: try youtube-transcript-api (manual/auto), then yt-dlp auto/author captions
- Removes timing tags and <c> ... </c> chunks
- De-duplicates repeated lines (common with raw dumps)
- Merges short caption fragments into full sentences / paragraphs
- Can also clean an existing captions text file (e.g., your sample)

Usage examples:
  python transcript_clean.py --url "https://www.youtube.com/watch?v=KuXjwB4LzSA" --out transcript.txt --format paragraphs
  python transcript_clean.py --file transcript.txt --out cleaned.txt --format sentences
"""

import argparse
import re
import sys
import os
import glob
import tempfile
import subprocess
import json
from typing import List, Optional, Tuple

# ------------------------- Fetch layer -------------------------

_YT_ID_RE = re.compile(r"(?:v=|/)([0-9A-Za-z_-]{11})(?:[&?/\s]|$)")

def is_youtube(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url

def extract_video_id(url: str) -> Optional[str]:
    m = _YT_ID_RE.search(url)
    return m.group(1) if m else None

def yt_api_lines(url: str, langs=None) -> Optional[List[str]]:
    """Try youtube-transcript-api; return list of caption lines or None."""
    if langs is None:
        langs = ["en", "en-US", "en-GB"]
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except Exception:
        return None

    vid = extract_video_id(url)
    if not vid:
        return None

    # try listing transcripts
    try:
        tlist = YouTubeTranscriptApi.list_transcripts(vid)
    except Exception:
        # try generic any-language pull
        try:
            chunks = YouTubeTranscriptApi.get_transcript(vid)
            return [c["text"].strip() for c in chunks if c.get("text", "").strip()]
        except Exception:
            return None

    # manual -> auto -> any
    for lang in langs:
        try:
            t = tlist.find_manually_created_transcript([lang])
            return [c["text"].strip() for c in t.fetch() if c.get("text", "").strip()]
        except Exception:
            pass
    for lang in langs:
        try:
            t = tlist.find_generated_transcript([lang])
            return [c["text"].strip() for c in t.fetch() if c.get("text", "").strip()]
        except Exception:
            pass
    try:
        for tr in tlist:
            try:
                return [c["text"].strip() for c in tr.fetch() if c.get("text", "").strip()]
            except Exception:
                continue
    except Exception:
        pass
    return None

def _run_yt_dlp_for_subs(url: str, sub_flag: str, lang: str, outdir: str) -> bool:
    # sub_flag = "--write-sub" (authored) or "--write-auto-sub"
    try:
        subprocess.check_output(
            [
                sys.executable, "-m", "yt_dlp",
                "--skip-download",
                sub_flag,
                f"--sub-langs={lang}",
                "--sub-format", "vtt/srt",
                "-o", os.path.join(outdir, "%(id)s.%(ext)s"),
                url,
            ],
            text=True, stderr=subprocess.STDOUT,
        )
        return True
    except subprocess.CalledProcessError:
        return False

_VTT_TS = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> ")
_SRT_TS = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3}\s-->\s\d{2}:\d{2}:\d{2},\d{3}$")

def _read_vtt_to_lines(path: str) -> List[str]:
    out = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            if s.startswith("WEBVTT") or "-->" in s:
                continue
            if s.isdigit():
                continue
            out.append(s)
    return out

def _read_srt_to_lines(path: str) -> List[str]:
    out = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            s = raw.strip()
            if not s or s.isdigit() or _SRT_TS.match(s):
                continue
            out.append(s)
    return out

def yt_dlp_lines(url: str, langs=None, prefer_auto=True) -> Optional[List[str]]:
    """Try yt-dlp to fetch authored/auto subs. Return list of lines or None."""
    if langs is None:
        langs = ["en", "en-US", "en-GB"]
    first, second = ("--write-auto-sub", "--write-sub") if prefer_auto else ("--write-sub", "--write-auto-sub")

    with tempfile.TemporaryDirectory() as td:
        for lang in langs + ["en.*", "all"]:
            for flag in (first, second):
                ok = _run_yt_dlp_for_subs(url, flag, lang, td)
                if not ok:
                    continue
                files = glob.glob(os.path.join(td, "*.vtt")) + glob.glob(os.path.join(td, "*.srt"))
                if not files:
                    continue
                # Prefer en-like if present
                en_like = [p for p in files if ".en." in p or p.endswith(".en.vtt") or p.endswith(".en.srt")]
                chosen = en_like[0] if en_like else files[0]
                return _read_vtt_to_lines(chosen) if chosen.endswith(".vtt") else _read_srt_to_lines(chosen)
    return None

def fetch_caption_lines(url: str, langs=None) -> List[str]:
    """Return raw caption lines (may be short fragments)."""
    if langs is None:
        langs = ["en", "en-US", "en-GB"]

    if is_youtube(url):
        lines = yt_api_lines(url, langs)
        if lines:
            return lines
    # fallback
    lines = yt_dlp_lines(url, langs=langs, prefer_auto=True)
    if lines:
        return lines
    raise RuntimeError("No subtitles/transcript available for this URL.")

# ------------------------- Clean/format layer -------------------------

# remove timing tags like <00:00:02.280> and <c>...</c> or <c.colorX>...</c>
TIMING_TAG = re.compile(r"<\d{2}:\d{2}:\d{2}(?:[.,]\d{3})?>")
C_TAG_OPEN = re.compile(r"<c(?:\.[^>]*)?>")
C_TAG_CLOSE = re.compile(r"</c>")

def strip_inline_markup(text: str) -> str:
    t = TIMING_TAG.sub("", text)
    t = C_TAG_OPEN.sub("", t)
    t = C_TAG_CLOSE.sub("", t)
    return " ".join(t.split())

def dedup_consecutive(lines: List[str], window: int = 3) -> List[str]:
    """Drop near-duplicate consecutive lines (window limits recent memory)."""
    out = []
    recent = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s in recent:
            continue
        out.append(s)
        recent.append(s)
        if len(recent) > window:
            recent.pop(0)
    return out

def merge_fragments_to_sentences(lines: List[str],
                                 max_sentence_len: int = 280,
                                 soft_end_re = re.compile(r"[.?!…]+$")) -> List[str]:
    """
    Greedily merge short caption fragments into sentences.
    Heuristics:
      - join until we hit punctuation, or we exceed max_sentence_len
      - capitalize starts if needed
    """
    def cap_start(s: str) -> str:
        return s[:1].upper() + s[1:] if s else s

    sentences = []
    buf = ""
    for raw in lines:
        frag = raw.strip()
        if not frag:
            continue
        # space join
        candidate = (buf + " " + frag).strip() if buf else frag
        if soft_end_re.search(frag) or len(candidate) >= max_sentence_len:
            # close sentence
            if not soft_end_re.search(candidate):
                candidate += "."
            sentences.append(candidate)
            buf = ""
        else:
            buf = candidate
    if buf:
        if not soft_end_re.search(buf):
            buf += "."
        sentences.append(buf)
    # normalize capitalization of sentence starts
    sentences = [cap_start(s.strip()) for s in sentences if s.strip()]
    return sentences

def group_sentences_to_paragraphs(sentences: List[str],
                                  max_par_len: int = 800) -> List[str]:
    """Pack sentences into paragraphs with a soft max length."""
    paras = []
    cur = ""
    for s in sentences:
        if not cur:
            cur = s
            continue
        candidate = f"{cur} {s}"
        if len(candidate) > max_par_len:
            paras.append(cur)
            cur = s
        else:
            cur = candidate
    if cur:
        paras.append(cur)
    return paras

def clean_lines_like_uploaded(raw_lines: List[str]) -> List[str]:
    """
    Your uploaded file had lines like:
      so<00:00:00.160><c> now</c>...
      and duplicates of plain/rendered lines.
    This function removes tags and dedups.
    """
    cleaned = [strip_inline_markup(x) for x in raw_lines]
    cleaned = [x for x in cleaned if x]  # drop empties
    cleaned = dedup_consecutive(cleaned, window=5)
    return cleaned

def clean_captions(raw_lines: List[str], out_format: str) -> List[str]:
    """
    out_format: 'lines' | 'sentences' | 'paragraphs'
    """
    cleaned_lines = clean_lines_like_uploaded(raw_lines)
    if out_format == "lines":
        return cleaned_lines
    sentences = merge_fragments_to_sentences(cleaned_lines)
    if out_format == "sentences":
        return sentences
    paras = group_sentences_to_paragraphs(sentences)
    return paras

# ------------------------- CLI -------------------------

def read_raw_lines_from_file(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [ln.rstrip("\n") for ln in f]

def write_out(seq: List[str], out_path: Optional[str]):
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            if seq and isinstance(seq[0], str):
                f.write("\n".join(seq))
        print(f"Saved {len(seq)} lines -> {out_path}")
    else:
        for s in seq:
            print(s)

def main():
    ap = argparse.ArgumentParser(description="Fetch and clean video transcripts into readable text.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="Video URL (YouTube or any site with subs via yt-dlp)")
    src.add_argument("--file", help="Clean an existing captions text file (like your raw dump)")
    ap.add_argument("--format", choices=["lines", "sentences", "paragraphs"], default="sentences",
                    help="Output structure (default: sentences)")
    ap.add_argument("--out", help="Write to a file instead of printing")
    ap.add_argument("--prefer", default="en,en-US,en-GB", help="Comma-separated language priority")
    args = ap.parse_args()

    langs = [x.strip() for x in args.prefer.split(",") if x.strip()]

    if args.url:
        try:
            raw = fetch_caption_lines(args.url, langs=langs)
        except Exception as e:
            sys.stderr.write(f"ERROR: {e}\n")
            sys.exit(2)
        out_seq = clean_captions(raw, args.format)
        write_out(out_seq, args.out)
    else:
        # Clean an existing file (like your uploaded transcript)
        raw_lines = read_raw_lines_from_file(args.file)
        out_seq = clean_captions(raw_lines, args.format)
        write_out(out_seq, args.out)

if __name__ == "__main__":
    main()
