# RoadmapGeneration/agents/prerequisite_inference.py
"""
Reasoning agent: infer prerequisite edges (src -> tgt) using directional heuristics.

- Label-subset and label-in-summary evidence
- Specificity heuristic (short/generic labels -> prerequisites)
- Optional embedding similarity as supportive evidence
- Conservative thresholding, cycle removal, transitive reduction
- Preserves node attributes
"""

import logging
import re
from typing import List, Dict, Any
import networkx as nx

logger = logging.getLogger(__name__)

# Optional embedding support
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    _EMBED = SentenceTransformer("all-MiniLM-L6-v2")
    HAVE_EMBED = True
except Exception:
    _EMBED = None
    HAVE_EMBED = False


def _tokenize(text: str):
    if not text:
        return []
    return re.findall(r'\w+', text.lower())


def _label_subset_score(src_label: str, tgt_label: str) -> float:
    a = _tokenize(src_label); b = _tokenize(tgt_label)
    if not a or not b:
        return 0.0
    matched = sum(1 for t in a if t in b)
    return matched / len(a)


def _label_in_summary_score(src_label: str, tgt_summary: str) -> float:
    a = _tokenize(src_label); s = _tokenize(tgt_summary)
    if not a or not s:
        return 0.0
    matched = sum(1 for t in a if t in s)
    return matched / len(a)


def _specificity(label: str) -> float:
    tokens = _tokenize(label)
    if not tokens:
        return 0.5
    generic = {"introduction", "intro", "overview", "background", "basics", "fundamentals", "concepts"}
    gen = sum(1 for t in tokens if t in generic)
    length_factor = min(1.0, len(tokens) / 6.0)
    return max(0.0, length_factor - 0.25 * gen)


def _embedding_sim(a_text: str, b_text: str) -> float:
    if not HAVE_EMBED or not a_text or not b_text:
        return 0.0
    try:
        a = _EMBED.encode([a_text])[0]; b = _EMBED.encode([b_text])[0]
        import numpy as np
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        sim = float(np.dot(a, b) / denom)
        return max(0.0, (sim + 1) / 2.0)
    except Exception as e:
        logger.debug("embedding error: %s", e)
        return 0.0


def _ensemble_score(src: Dict[str, Any], tgt: Dict[str, Any]) -> float:
    w_subset = 0.45
    w_label_summary = 0.30
    w_spec = 0.15
    w_emb = 0.10

    s_subset = _label_subset_score(src.get("label", ""), tgt.get("label", ""))
    s_label_sum = _label_in_summary_score(src.get("label", ""), tgt.get("summary", ""))
    spec_src = _specificity(src.get("label", ""))
    spec_tgt = _specificity(tgt.get("label", ""))
    spec_dir = max(0.0, min(1.0, spec_tgt - spec_src))
    emb = _embedding_sim(src.get("summary", "") or src.get("label", ""), tgt.get("summary", "") or tgt.get("label", ""))

    score = (w_subset * s_subset + w_label_summary * s_label_sum + w_spec * spec_dir + w_emb * emb)
    return float(score)


def prerequisite_inference(nodes: List[Dict[str, Any]], score_threshold: float = 0.40) -> nx.DiGraph:
    """
    Build DAG of prerequisites. Returns a DiGraph with node attributes preserved.
    """
    G = nx.DiGraph()
    for n in nodes:
        nid = str(n.get("id") or n.get("label"))
        G.add_node(nid, **n)

    # compute edges
    for i, src in enumerate(nodes):
        for j, tgt in enumerate(nodes):
            if i == j:
                continue
            score = _ensemble_score(src, tgt)
            if score >= score_threshold:
                G.add_edge(str(src.get("id")), str(tgt.get("id")), confidence=score)

    # remove cycles by removing lowest-confidence edges in cycles iteratively
    try:
        while True:
            try:
                cycle = list(nx.find_cycle(G))
            except nx.NetworkXNoCycle:
                break
            if not cycle:
                break
            min_edge = None; min_conf = None
            for u, v in cycle:
                conf = G.edges[u, v].get("confidence", 0.0)
                if min_conf is None or conf < min_conf:
                    min_conf = conf; min_edge = (u, v)
            if min_edge:
                G.remove_edge(*min_edge)
            else:
                break
    except Exception as e:
        logger.debug("cycle removal error: %s", e)

    # transitive reduction while preserving node data
    try:
        TR = nx.transitive_reduction(G)
        for n, attrs in G.nodes(data=True):
            if n in TR.nodes:
                TR.nodes[n].update(attrs)
        return TR
    except Exception:
        return G
