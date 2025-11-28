import re
import argparse
from collections import Counter
import spacy

# Load spaCy model (make sure to run: python -m spacy download en_core_web_sm)
nlp = spacy.load("en_core_web_sm")

# Bloom's Taxonomy templates
BLOOM_TEMPLATES = {
    "Remember": [
        "List the key points mentioned about {topic}.",
        "Define what {topic} is in your own words."
    ],
    "Understand": [
        "Explain why {topic} is important according to the transcript.",
        "Summarize the main ideas about {topic}."
    ],
    "Apply": [
        "Give a real-world example of how {topic} can be applied.",
        "Demonstrate how principles of {topic} could be used in real scenarios."
    ],
    "Analyze": [
        "Compare {topic} with another related concept.",
        "Analyze the challenges of implementing {topic}."
    ],
    "Evaluate": [
        "Assess the strengths and weaknesses of {topic}.",
        "Do you agree with the perspective on {topic}? Justify your answer."
    ],
    "Create": [
        "Design a new project plan that incorporates {topic}.",
        "Propose new practices or improvements based on {topic} principles."
    ]
}

def clean_transcript(text: str) -> str:
    """Remove tags like <00:00:..> and <c>..</c> and return plain text"""
    text = re.sub(r"<[^>]+>", "", text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return " ".join(lines)

def extract_topic(transcript: str) -> str:
    """
    Extract the most likely topic using noun phrases (spaCy).
    Falls back to most frequent content word if none found.
    """
    doc = nlp(transcript)

    # collect noun chunks (multi-word phrases like "extreme programming")
    noun_phrases = [chunk.text.strip() for chunk in doc.noun_chunks if len(chunk.text.strip().split()) > 1]

    if noun_phrases:
        common = Counter(noun_phrases).most_common(1)
        return common[0][0]

    # fallback: pick most frequent non-stopword noun
    words = [t.text for t in doc if t.pos_ in ("NOUN", "PROPN") and not t.is_stop]
    if words:
        common = Counter(words).most_common(1)
        return common[0][0]

    return "the topic"

def generate_questions(transcript: str):
    clean_text = clean_transcript(transcript)
    topic = extract_topic(clean_text)
    results = {}
    for level, templates in BLOOM_TEMPLATES.items():
        results[level] = [t.format(topic=topic) for t in templates]
    return topic, results

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate Bloom's questions from a transcript")
    ap.add_argument("--file", required=True, help="Transcript text file")
    args = ap.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    topic, questions = generate_questions(raw_text)

    print(f"\n📌 Detected Topic: {topic}\n")
    for level, qs in questions.items():
        print(f"=== {level} ===")
        for q in qs:
            print(f"- {q}")
        print()
