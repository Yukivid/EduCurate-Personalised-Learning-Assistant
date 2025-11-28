# RoadmapGeneration/agents/topic_decomposer.py
"""
Perception agent: GeminiRoadmapAgent (LLM-first) with HF fallback.

- Use a finetuned HF seq2seq model (optional) for deterministic outputs
- Use a Gemini (or any LLM) client with few-shot prompt examples as primary generator
- Parse LLM output robustly into an ordered list of subtopics
- Emit nodes with fields: id,label,summary,keywords,dependencies,sources,embedding
- Optional: compute embeddings using sentence-transformers if installed
"""

import json
import logging
import os
import re
from typing import Any, List, Dict, Optional
import uuid
import logging
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Optional embedding model (best-effort)
try:
    from sentence_transformers import SentenceTransformer
    _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    HAVE_EMBED = True
except Exception:
    _EMBED_MODEL = None
    HAVE_EMBED = False

# Optional HF seq2seq (T5) imports
HF_AVAILABLE = False
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    HF_AVAILABLE = True
except Exception:
    HF_AVAILABLE = False


# -------------------------
# Helpers: parse LLM/hf text outputs
# -------------------------
def parse_roadmap_text(text: str) -> List[str]:
    """
    Robustly extract an ordered list of subtopics from various outputs:
     - JSON array
     - "Topic Names: [A, B, C]"
     - numbered/bulleted lists
     - plain comma-separated lists

    Returns list of non-empty strings (trimmed).
    """
    if not text:
        return []
    original = text
    text = text.strip()

    # Try JSON
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
        if isinstance(parsed, dict):
            # try obvious keys
            for k in ("topics", "items", "sections"):
                if k in parsed and isinstance(parsed[k], list):
                    return [str(x).strip() for x in parsed[k] if str(x).strip()]
    except Exception:
        pass

    # Find explicit "Topic Names: [...]", or bracketed list anywhere
    m = re.search(r"\[.*\]", text, flags=re.S)
    if m:
        inner = m.group(0).strip("[] \n\t")
        parts = re.split(r"[,\n\u2022;]+", inner)
        result = [p.strip() for p in parts if p.strip()]
        if result:
            return result

    # Remove headers like "Topic Names:" or "Output:"
    text = re.sub(r"(?i)^.*topic names\s*:\s*", "", original).strip()
    # Replace newlines/bullets with commas
    text = re.sub(r"[\r\n\u2022\-]+", ", ", text)
    # Split on commas or numbered prefixes
    parts = re.split(r",\s*|\d+\.\s*", text)
    cleaned = [p.strip() for p in parts if len(p.strip()) > 2]
    # Deduplicate preserving order
    seen = set()
    out = []
    for s in cleaned:
        if s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out


# LLM adapter & few-shot
def _call_llm(llm_client: Any, prompt: str) -> str:
    """
    Flexible adapter to call different LLM SDK shapes.
    Accepts:
    - callable(prompt) -> str
    - object with .generate(prompt=...) -> response (with .text or .candidates)
    - object with .generate_content(prompt) (genai style)
    """
    if llm_client is None:
        raise ValueError("llm_client is None")

    # 1) simple callable
    try:
        if callable(llm_client):
            out = llm_client(prompt)
            return out if isinstance(out, str) else str(out)
    except Exception as e:
        logger.debug("llm callable failed: %s", e)

    # 2) google genai style: .generate_content
    try:
        gen = getattr(llm_client, "generate_content", None)
        if callable(gen):
            resp = gen(prompt)
            # genai returns response with candidates → content parts
            # try multiple extraction strategies
            try:
                if hasattr(resp, "candidates") and resp.candidates:
                    candidate = resp.candidates[0]
                    # nested content.parts[0].text in some SDKs
                    txt = None
                    if hasattr(candidate, "content"):
                        if isinstance(candidate.content, list) and candidate.content:
                            first = candidate.content[0]
                            txt = getattr(first, "text", None) or getattr(first, "content", None)
                    if txt is None:
                        txt = getattr(candidate, "text", None) or str(candidate)
                    return txt if isinstance(txt, str) else str(txt)
                if hasattr(resp, "text"):
                    return resp.text
                return str(resp)
            except Exception:
                return str(resp)
    except Exception as e:
        logger.debug("llm.generate_content failed: %s", e)

    # 3) .generate (OpenAI-like or other)
    try:
        gen2 = getattr(llm_client, "generate", None)
        if callable(gen2):
            res = gen2(prompt=prompt) if _accepts_kwarg(gen2, "prompt") else gen2(prompt)
            if isinstance(res, str):
                return res
            if hasattr(res, "text"):
                return res.text
            return str(res)
    except Exception as e:
        logger.debug("llm.generate failed: %s", e)

    # 4) .__call__
    try:
        if hasattr(llm_client, "__call__"):
            out = llm_client(prompt)
            return out if isinstance(out, str) else str(out)
    except Exception as e:
        logger.debug("llm.__call__ failed: %s", e)

    raise ValueError("Unsupported llm_client shape; provide callable or object with generate()/generate_content().")


def _accepts_kwarg(func, name: str) -> bool:
    """Best-effort check if a function signature accepts a named arg."""
    try:
        import inspect
        sig = inspect.signature(func)
        return name in sig.parameters
    except Exception:
        return False


class GeminiRoadmapAgent:
    def __init__(self, gemini_client):
        self.client = gemini_client
        self.logger = logging.getLogger(__name__)

    def generate_subtopics(self, topic: str):
        """
        Generate topic-specific subtopics using Gemini API.
        Returns a list of dict nodes with {id, label, summary}.
        """
        try:
            prompt = (
                f"You are an expert course planner AI.\n"
                f"Given the topic '{topic}', list all major learning subtopics in the correct order "
                f"needed to master it. For each subtopic, also include a one-sentence summary.\n"
                f"Respond in this format:\n"
                f"1. <Subtopic Name>: <One sentence summary>\n"
                f"2. ... etc.\n"
            )

            response = self.client.generate_content(prompt)

            # Extract plain text safely
            text = ""
            if hasattr(response, "text"):
                text = response.text
            elif hasattr(response, "candidates") and response.candidates:
                text = response.candidates[0].content.parts[0].text.strip()
            else:
                text = str(response)

            # Parse into structured nodes
            nodes = self._parse_subtopics(text)
            return nodes

        except Exception as e:
            self.logger.exception(f"❌ Gemini subtopic generation failed: {e}")
            return [{"id": str(uuid.uuid4()), "label": topic, "summary": "General overview of topic."}]

    def _parse_subtopics(self, text: str):
        """
        Parse Gemini's numbered response into structured topic nodes.
        """
        nodes = []
        for line in text.splitlines():
            line = line.strip()
            match = re.match(r"^\d+\.\s*(.+?):\s*(.+)$", line)
            if match:
                label = match.group(1).strip()
                summary = match.group(2).strip()
                nodes.append({
                    "id": str(uuid.uuid4()),
                    "label": label,
                    "summary": summary
                })

        # If parsing fails, fallback to treating lines as topics
        if not nodes and text:
            for t in re.split(r'[\n,;-]+', text):
                t = t.strip()
                if t:
                    nodes.append({
                        "id": str(uuid.uuid4()),
                        "label": t,
                        "summary": f"Subtopic related to {t}"
                    })

        return nodes

# HF seq2seq wrapper
class HFSeq2SeqRoadmap:
    """
    Optional local finetuned seq2seq wrapper (T5, T0, etc.)
    Provide hf_model_path to use; requires transformers + torch.
    """

    def __init__(self, hf_model_path: Optional[str] = None, device: Optional[str] = None):
        self.hf_model = None
        self.tokenizer = None
        self.device = device or ("cuda" if HF_AVAILABLE and torch.cuda.is_available() else "cpu")
        if hf_model_path and HF_AVAILABLE:
            try:
                logger.info("Loading HF roadmap model from %s", hf_model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(hf_model_path, use_fast=True)
                self.hf_model = AutoModelForSeq2SeqLM.from_pretrained(hf_model_path).to(self.device)
            except Exception as e:
                logger.warning("Failed to load HF model: %s", e)
                self.hf_model = None

    def generate(self, topic: str, max_length: int = 256) -> List[str]:
        if not self.hf_model:
            return []
        try:
            txt = f"Generate an ordered roadmap for mastering: {topic}\nOutput format: Topic Names: [A, B, C]"
            inputs = self.tokenizer(txt, return_tensors="pt", truncation=True).to(self.device)
            with torch.no_grad():
                out = self.hf_model.generate(**inputs, max_length=max_length, num_beams=4, early_stopping=True)
            text = self.tokenizer.decode(out[0], skip_special_tokens=True)
            return parse_roadmap_text(text)
        except Exception as e:
            logger.warning("HF generate error: %s", e)
            return []


# Public function
def topic_decomposer(topic: str,
                     llm_client: Optional[Any] = None,
                     hf_model_path: Optional[str] = None,
                     examples_path: Optional[str] = None,
                     n_sections: int = 8) -> List[Dict]:
    """
    Top-level decomposer. Try HF seq2seq first (if path given and available),
    then Gemini/LLM few-shot, then deterministic fallback.
    Returns list of nodes with stable ids and minimal metadata.
    """
    nodes: List[Dict] = []

    # 1) Try HF seq2seq if available
    if hf_model_path and HF_AVAILABLE:
        hf_wrapper = HFSeq2SeqRoadmap(hf_model_path=hf_model_path)
        out = hf_wrapper.generate(topic, max_length=256)
        if out:
            topics = out[:n_sections]
        else:
            topics = []
    else:
        topics = []

    # 2) If HF didn't produce, try Gemini/LLM few-shot
    if not topics and llm_client:
        agent = GeminiRoadmapAgent(llm_client=llm_client, examples_path=examples_path)
        topics = agent.generate(topic)[:n_sections]

    # 3) Fallback deterministic planner (domain-aware)
    if not topics:
        # Minimal deterministic expansion with domain specializations
        q = topic.lower()
        if any(k in q for k in ["sort", "sorting", "merge", "quicksort"]):
            topics = [
                "Introduction to Sorting",
                "Comparison sorts and properties",
                "Divide and Conquer and Recursion",
                "Merge Sort - algorithm and example",
                "Complexity analysis of Merge Sort",
                "In-place vs external variants",
                "Applications and optimizations"
            ]
        elif any(k in q for k in ["cnn", "convolutional", "convnet"]):
            topics = [
                "Prerequisite math for CNNs",
                "Neural network basics",
                "Convolution and pooling operations",
                "Core CNN architectures",
                "Training CNNs and regularization",
                "Transfer learning and modern architectures",
                "Object detection and segmentation"
            ]
        elif any(k in q for k in ["decision tree", "decision trees", "tree"]):
            topics = [
                "Prerequisite mathematics for decision trees",
                "Entropy and information gain",
                "Tree construction algorithms (ID3/CART)",
                "Overfitting and pruning",
                "Ensemble methods: Random Forests",
                "Performance metrics and applications"
            ]
        else:
            # generic but slightly expanded
            topics = [
                f"Introduction and motivation for {topic}",
                "Prerequisite concepts and mathematics",
                f"Core concepts of {topic}",
                f"Implementation patterns for {topic}",
                f"Analysis and complexity of {topic}",
                f"Advanced topics and extensions for {topic}",
                f"Applications and case studies of {topic}"
            ]
        topics = topics[:n_sections]

    # Build node objects, compute embeddings if available
    for i, t in enumerate(topics):
        summary = f"{t} — a focused section for mastering {topic}."
        emb = []
        if HAVE_EMBED:
            try:
                emb = _EMBED_MODEL.encode([summary])[0].tolist()
            except Exception:
                emb = []
        nodes.append({
            "id": str(i),
            "label": t,
            "summary": summary,
            "keywords": [],
            "dependencies": [],  # explicit dependencies can be filled by user/LLM later
            "sources": ["hf" if (hf_model_path and HF_AVAILABLE and i < len(topics)) else "llm" if llm_client else "rule"],
            "embedding": emb
        })

    # Attempt to fill simple sequential dependencies if none present
    for i in range(1, len(nodes)):
        if not nodes[i].get("dependencies"):
            nodes[i]["dependencies"] = [nodes[i-1]["label"]]

    return nodes
