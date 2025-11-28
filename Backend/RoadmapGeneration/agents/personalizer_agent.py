# RoadmapGeneration/agents/personalizer_agent.py
"""
Personalizer agent:

- Removes mastered nodes (by id or label) from graph
- Produces ordered schedule based on topological order and difficulty
- Adapts estimated times to user time_budget and learning_speed
- Returns list of schedule items with dependencies & summaries
"""

import networkx as nx
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


def personalizer_agent(G: nx.DiGraph, user_model: Dict[str, Any], time_budget: float = 0.0) -> List[Dict[str, Any]]:
    mastered = set(user_model.get("mastered_nodes", []) or [])
    learning_speed = float(user_model.get("learning_speed", 1.0) or 1.0)
    time_budget = float(time_budget or 0)

    # Remove mastered nodes (match by id or label)
    to_remove = []
    for nid, data in list(G.nodes(data=True)):
        if nid in mastered or data.get("label") in mastered:
            to_remove.append(nid)
    if to_remove:
        G.remove_nodes_from(to_remove)

    if not G.nodes():
        return [{"topic": "All topics mastered", "difficulty": 0.0, "recommended_time": 0.0, "dependencies": []}]

    # Use topological order when possible
    try:
        order = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        order = list(G.nodes())

    schedule = []
    total_default = 0.0
    for nid in order:
        meta = G.nodes[nid]
        label = meta.get("label", str(nid))
        difficulty = float(meta.get("difficulty_score", 3.0))
        est = float(meta.get("est_time", max(5.0, difficulty * 5.0)))
        deps = [G.nodes[p].get("label", p) for p in G.predecessors(nid)]
        schedule.append({
            "id": nid,
            "topic": label,
            "difficulty": round(difficulty, 2),
            "recommended_time": round(est, 2),
            "dependencies": deps,
            "summary": meta.get("summary", "")
        })
        total_default += est

    # Scale to time budget if provided (respect learning speed)
    if time_budget and total_default > 0:
        scale = (time_budget / total_default) / learning_speed
        for item in schedule:
            item["recommended_time"] = round(max(1.0, item["recommended_time"] * scale), 2)

    return schedule
