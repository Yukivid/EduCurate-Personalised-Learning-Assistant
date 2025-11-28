from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

from ..core.types import PipelineInput
from ..agents.retriever import RetrieverAgent
from ..agents.model_generator import ModelGeneratorAgent
from ..agents.rubric_generator import RubricGeneratorAgent
from ..agents.evaluator import EvaluatorAgent
from ..agents.reflector import ReflectorAgent
from ..agents.aggregator import Aggregator
from ..pipeline.graph import build_graph


app = FastAPI(title="Auto-Eval MCP Server", version="0.1.0")


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5


class GradeRequest(BaseModel):
    question: str
    student_answer: str
    context: Optional[str] = ""
    candidate_rubric: Optional[str] = None


class RunRequest(BaseModel):
    question: str
    student_answer: str
    top_k: int = 5
    use_graph: bool = True


@app.post("/retrieve")
def retrieve(req: RetrieveRequest) -> Dict[str, Any]:
    retriever = RetrieverAgent()
    rr = retriever.retrieve(req.query, req.top_k)
    return rr.model_dump()


@app.post("/grade")
def grade(req: GradeRequest) -> Dict[str, Any]:
    model_gen = ModelGeneratorAgent()
    rubric_gen = RubricGeneratorAgent()
    evaluator = EvaluatorAgent()

    passages_text = req.context or ""
    if not req.candidate_rubric:
        ma = model_gen.generate(req.question, req.student_answer, passages_text)
        candidate = ma.candidate_rubric
        model_answer_text = ma.answer
    else:
        candidate = req.candidate_rubric
        model_answer_text = ""

    rubric = rubric_gen.finalize(candidate)
    evaluation = evaluator.evaluate(req.question, req.student_answer, model_answer_text, rubric.rubric_text, passages_text)
    return {
        "rubric": rubric.model_dump(),
        "evaluation": evaluation.model_dump(),
    }


@app.post("/run")
def run(req: RunRequest) -> Dict[str, Any]:
    inp = PipelineInput(question=req.question, student_answer=req.student_answer, top_k=req.top_k)
    retriever = RetrieverAgent()
    model_gen = ModelGeneratorAgent()
    rubric_gen = RubricGeneratorAgent()
    evaluator = EvaluatorAgent()
    reflector = ReflectorAgent()
    aggregator = Aggregator()

    if req.use_graph:
        graph = build_graph()
        state = {
            "question": inp.question,
            "student_answer": inp.student_answer,
            "top_k": inp.top_k,
            "retriever": retriever,
            "model_gen": model_gen,
            "rubric_gen": rubric_gen,
            "evaluator": evaluator,
            "reflector": reflector,
            "aggregator": aggregator,
        }
        out = graph.invoke(state)
        return out["result"].model_dump()

    # Non-graph fallback
    retrieved = retriever.retrieve(inp.question, inp.top_k)
    passages_text = "\n".join(p.text for p in retrieved.passages)
    model_answer = model_gen.generate(inp.question, inp.student_answer, passages_text)
    rubric = rubric_gen.finalize(model_answer.candidate_rubric)
    evaluation = evaluator.evaluate(inp.question, inp.student_answer, model_answer.answer, rubric.rubric_text, passages_text)
    reflection = reflector.reflect(passages_text, evaluation.feedback)
    confidence = evaluation.confidence or 0.0
    if reflection.confidence_adjustment:
        confidence = max(0.0, min(1.0, confidence + reflection.confidence_adjustment))
    result = aggregator.aggregate(
        evaluation.score,
        evaluation.feedback,
        model_answer.answer,
        rubric.rubric_text,
        [p.id for p in retrieved.passages],
        confidence,
    )
    return result.model_dump()



