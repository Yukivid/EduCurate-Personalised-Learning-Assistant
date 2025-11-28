import re
import argparse
import random
from rapidfuzz import fuzz
import spacy

# load spaCy model
nlp = spacy.load("en_core_web_sm")

# -------------------------
# Utility
# -------------------------
def clean_transcript(text: str) -> str:
    """Remove tags and join transcript lines."""
    text = re.sub(r"<[^>]+>", "", text)  # remove XML-like tags
    return " ".join([ln.strip() for ln in text.splitlines() if ln.strip()])


def split_sentences(text: str):
    """Split transcript into sentences."""
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 15]


# -------------------------
# Question generation rules
# -------------------------
def generate_questions(sent):
    """Generate Bloom-level questions from a transcript sentence."""
    doc = nlp(sent)
    questions = []

    # ---- Remember: Definition ----
    for tok in doc:
        if tok.lemma_ == "be" and tok.pos_ == "VERB":
            subj = [w.text for w in tok.lefts if w.dep_.startswith("nsubj")]
            if subj:
                subj_text = subj[0]
                pred_text = " ".join([t.text for t in tok.rights])
                if subj_text and pred_text:
                    q = f"What is {subj_text}?"
                    questions.append(("Remember", q, pred_text, sent))
                    break

    # ---- Understand: Fill-in-the-blank ----
    chunks = list(doc.noun_chunks)  # FIX: convert generator → list
    if len(chunks) > 0:
        chunk = max(chunks, key=lambda c: len(c.text))  # pick longest noun phrase
        ans = chunk.text
        q_text = sent.replace(ans, "_____")
        q = f"Fill in the blank: {q_text}"
        questions.append(("Understand", q, ans, sent))

    # ---- Apply: Numeric fact ----
    nums = [t.text for t in doc if t.like_num]
    if nums:
        q = f"What numeric value is mentioned in: \"{sent}\"?"
        questions.append(("Apply", q, nums[0], sent))

    # ---- Analyze: Entity-based MCQ ----
    if doc.ents:
        ent = doc.ents[0]
        ans = ent.text
        q_text = sent.replace(ans, "_____")
        distractors = ["Sorting", "Algorithm", "Python", "Recursion"]
        options = [ans] + random.sample(distractors, k=3)
        random.shuffle(options)
        q = f"Analyze: Fill the blank in: {q_text}\nOptions: {', '.join(options)}"
        questions.append(("Analyze", q, ans, sent))

    # ---- Evaluate: Why/How ----
    if "because" in sent.lower() or "so that" in sent.lower():
        q = f"Why: {sent}?"
        questions.append(("Evaluate", q, sent, sent))

    # ---- Create: Open-ended design ----
    if "algorithm" in sent.lower():
        q = f"Propose a modification to improve: {sent}"
        questions.append(("Create", q, sent, sent))

    return questions


# -------------------------
# Answer evaluation
# -------------------------
def evaluate_answer(user_answer, correct_answer):
    """Check if user answer matches expected answer (fuzzy)."""
    score = fuzz.token_set_ratio(user_answer.lower(), correct_answer.lower())
    return score >= 65


# -------------------------
# Run Quiz
# -------------------------
def run_quiz(transcript, num_qs=6):
    sentences = split_sentences(transcript)
    all_qs = []
    for s in sentences:
        qs = generate_questions(s)
        all_qs.extend(qs)

    if not all_qs:
        print("No questions could be generated.")
        return

    chosen = random.sample(all_qs, min(num_qs, len(all_qs)))
    score = 0

    print("\n--- Bloom’s Taxonomy Quiz ---\n")
    for i, (level, q, ans, ref) in enumerate(chosen, 1):
        print(f"Q{i} ({level}): {q}")
        user = input("Your answer: ")
        if evaluate_answer(user, str(ans)):
            print("✅ Correct!")
            score += 1
        else:
            print(f"❌ Not quite. Reference: {ref}")
            print(f"Expected: {ans}")
        print("-" * 40)

    print(f"\nFinal Score: {score}/{len(chosen)}")


# -------------------------
# CLI
# -------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Bloom Quiz from Transcript")
    ap.add_argument("--file", required=True, help="Transcript file")
    ap.add_argument("--num", type=int, default=6, help="Number of questions")
    args = ap.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        raw = f.read()

    transcript = clean_transcript(raw)
    run_quiz(transcript, args.num)
