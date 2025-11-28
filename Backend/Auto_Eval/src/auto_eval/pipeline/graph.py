from typing import Dict, Any
from langgraph.graph import StateGraph, END

from ..agents.retriever import RetrieverAgent
from ..agents.model_generator import ModelGeneratorAgent
from ..agents.rubric_generator import RubricGeneratorAgent
from ..agents.evaluator import EvaluatorAgent
from ..agents.reflector import ReflectorAgent
from ..agents.aggregator import Aggregator


def build_graph() -> Any:
    """
    Builds the LangGraph-based multi-agent AutoEval pipeline.
    Each node corresponds to an agent step, and the state dictionary
    is passed and expanded through all nodes.
    """

    graph = StateGraph(dict)

    # --- NODE 1: RETRIEVE ---
    def n_retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
        retriever: RetrieverAgent = state["retriever"]
        top_k: int = state.get("top_k", 5)
        rr = retriever.retrieve(state["question"], top_k)
        passages_text = "\n".join(p.text for p in rr.passages)
        return {**state, "retrieved": rr, "passages_text": passages_text}

    # --- NODE 2: MODEL GENERATOR ---
    def n_model(state: Dict[str, Any]) -> Dict[str, Any]:
        model_gen: ModelGeneratorAgent = state["model_gen"]
        ma = model_gen.generate(
            state["question"],
            state["student_answer"],
            state.get("passages_text", "")
        )
        return {**state, "model_answer": ma}

    # --- NODE 3: RUBRIC GENERATOR ---
    def n_rubric(state: Dict[str, Any]) -> Dict[str, Any]:
        rubric_gen: RubricGeneratorAgent = state["rubric_gen"]
        ru = rubric_gen.finalize(state["model_answer"].candidate_rubric)
        return {**state, "rubric": ru}

    # --- NODE 4: EVALUATOR ---
    def n_evaluate(state: Dict[str, Any]) -> Dict[str, Any]:
        evaluator: EvaluatorAgent = state["evaluator"]
        ev = evaluator.evaluate(
            state["question"],
            state["student_answer"],
            state["model_answer"].answer,
            state["rubric"].rubric_text,
            state.get("passages_text", "")
        )
        return {**state, "evaluation": ev}

    # --- NODE 5: REFLECTOR ---
    def n_reflect(state: Dict[str, Any]) -> Dict[str, Any]:
        reflector: ReflectorAgent = state["reflector"]
        rf = reflector.reflect(
            state.get("passages_text", ""),
            state["evaluation"].feedback
        )
        return {**state, "reflection": rf}

    # --- NODE 6: AGGREGATOR ---
    def n_aggregate(state: Dict[str, Any]) -> Dict[str, Any]:
        aggregator: Aggregator = state["aggregator"]

        rr = state.get("retrieved")
        provenance = [p.id for p in (rr.passages if rr else [])]

        confidence = state["evaluation"].confidence or 0.0
        if state.get("reflection") and state["reflection"].confidence_adjustment:
            confidence = max(
                0.0,
                min(1.0, confidence + (state["reflection"].confidence_adjustment or 0.0))
            )

        result = aggregator.aggregate(
            state["evaluation"].score,
            state["evaluation"].feedback,
            state["model_answer"].answer,
            state["rubric"].rubric_text,
            provenance,
            confidence
        )
        return {**state, "result": result}

    # --- GRAPH CONNECTIONS ---
    graph.add_node("retrieve", n_retrieve)
    graph.add_node("model", n_model)
    graph.add_node("rubric", n_rubric)
    graph.add_node("evaluate", n_evaluate)
    graph.add_node("reflect", n_reflect)
    graph.add_node("aggregate", n_aggregate)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "model")
    graph.add_edge("model", "rubric")
    graph.add_edge("rubric", "evaluate")
    graph.add_edge("evaluate", "reflect")
    graph.add_edge("reflect", "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()