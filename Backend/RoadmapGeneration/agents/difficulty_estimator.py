# RoadmapGeneration/agents/difficulty_estimator.py
"""
Action agent: estimate difficulty and recommended time per node.

- Computes simple textual readability (Flesch-ish) fallback
- Uses structural signals (number of prerequisites / ancestor depth)
- Adds: difficulty_score (1-10), est_time (minutes), confidence_interval
"""

import re
import logging
from typing import Tuple
import networkx as nx

logger = logging.getLogger(__name__)

# textstat optional
try:
    from textstat import flesch_kincaid_grade
    HAVE_TEXTSTAT = True
except Exception:
    HAVE_TEXTSTAT = False


def _simple_fk(text: str) -> float:
    words = re.findall(r'\w+', text or "")
    sentences = re.split(r'[.!?]+', text or "")
    sentences = [s for s in sentences if s.strip()]
    num_sent = max(1, len(sentences))
    num_words = max(1, len(words))
    syllables = sum(max(1, sum(ch in "aeiouy" for ch in w.lower())) for w in words)
    try:
        return 0.39 * (num_words / num_sent) + 11.8 * (syllables / num_words) - 15.59
    except Exception:
        return 8.0


def _extract_features(node: dict, G: nx.DiGraph) -> Tuple[float, int, int]:
    summary = node.get("summary", "") or ""
    if HAVE_TEXTSTAT:
        try:
            fk = flesch_kincaid_grade(summary)
        except Exception:
            fk = _simple_fk(summary)
    else:
        fk = _simple_fk(summary)
    length = len(re.findall(r'\w+', summary))
    nid = node.get("id")
    deps = len(list(G.predecessors(nid))) if nid in G.nodes else 0
    depth = len(list(nx.ancestors(G, nid))) if nid in G.nodes else 0
    structural = deps + depth
    return fk, length, structural


def _regressor(feats) -> Tuple[float, float, Tuple[float, float]]:
    fk, length, structural = feats
    difficulty = 1.0 + max(0.0, (fk / 12.0)) + min(6.0, structural * 0.8)
    difficulty = min(10.0, round(difficulty, 2))
    est_time = max(3.0, min(300.0, round((length * 0.35) + difficulty * 5.0, 2)))
    conf = (0.25, 0.85)
    return difficulty, est_time, conf


def difficulty_estimator(G: nx.DiGraph) -> nx.DiGraph:
    for nid in list(G.nodes()):
        meta = G.nodes[nid]
        feats = _extract_features(meta, G)
        difficulty, est_time, conf = _regressor(feats)
        meta["difficulty_score"] = difficulty
        meta["est_time"] = est_time
        meta["confidence_interval"] = conf
    return G
