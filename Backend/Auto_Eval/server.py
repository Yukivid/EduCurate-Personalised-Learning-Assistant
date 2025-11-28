# Auto_Eval/server.py
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Import from the correct module path
from src.auto_eval.core.types import PipelineInput
from src.auto_eval.agents.retriever import RetrieverAgent
from src.auto_eval.agents.model_generator import ModelGeneratorAgent
from src.auto_eval.agents.rubric_generator import RubricGeneratorAgent
from src.auto_eval.agents.evaluator import EvaluatorAgent
from src.auto_eval.agents.reflector import ReflectorAgent
from src.auto_eval.agents.aggregator import Aggregator
from src.auto_eval.pipeline.graph import build_graph

app = FastAPI(title="Auto-Eval MCP Server", version="0.1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
async def root():
    return {"message": "Auto-Eval MCP Server is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)