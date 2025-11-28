# RoadmapGeneration/agents/validator_agent.py
"""
Validator agent:

- Checks DAG acyclicity and attempts to break cycles via low-confidence edges removal
- Checks coverage for original keywords
- Detects missing summaries and other issues
- Returns (G, issues)
"""

import networkx as nx
import logging
from typing import Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


def _break_cycles_by_confidence(G: nx.DiGraph) -> nx.DiGraph:
    try:
        while True:
            try:
                cycle = list(nx.find_cycle(G))
            except nx.NetworkXNoCycle:
                break
            if not cycle:
                break
            min_e = None; min_conf = None
            for u, v in cycle:
                conf = G.edges[u, v].get("confidence", 0.0)
                if min_conf is None or conf < min_conf:
                    min_conf = conf; min_e = (u, v)
            if min_e:
                G.remove_edge(*min_e)
            else:
                break
    except Exception as e:
        logger.debug("cycle break error: %s", e)
    return G


def validator_agent(G: nx.DiGraph, original_keywords: List[str] = None) -> Tuple[nx.DiGraph, List[Dict[str, Any]]]:
    issues: List[Dict[str, Any]] = []

    # 1) cycle detection & attempt to fix
    if not nx.is_directed_acyclic_graph(G):
        issues.append({"type": "cycle", "severity": "high", "suggested_fix": "attempting to remove low-confidence edges"})
        G = _break_cycles_by_confidence(G)
        if not nx.is_directed_acyclic_graph(G):
            issues.append({"type": "cycle_remaining", "severity": "critical", "suggested_fix": "manual review required"})

    # 2) coverage check for original keywords
    node_labels = [d.get("label", "").lower() for _, d in G.nodes(data=True)]
    for kw in (original_keywords or []):
        if kw.lower() not in " ".join(node_labels):
            issues.append({"type": "missing_keyword", "keyword": kw, "severity": "medium", "suggested_fix": f"add node for {kw}"})

    # 3) missing summary detection
    for n, d in G.nodes(data=True):
        if not d.get("summary"):
            issues.append({"type": "missing_summary", "node": n, "severity": "low", "suggested_fix": "generate summary via LLM"})

    return G, issues
