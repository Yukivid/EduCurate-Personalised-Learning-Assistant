# routes/evaluation.py
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
import models

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Auto_Eval", "src")))

try:
    from auto_eval.core.types import PipelineInput
    from auto_eval.pipeline.graph import build_graph
    from auto_eval.agents.retriever import RetrieverAgent
    from auto_eval.agents.model_generator import ModelGeneratorAgent
    from auto_eval.agents.rubric_generator import RubricGeneratorAgent
    from auto_eval.agents.evaluator import EvaluatorAgent
    from auto_eval.agents.reflector import ReflectorAgent
    from auto_eval.agents.aggregator import Aggregator
except Exception as e:
    raise ImportError(f"❌ Failed to import Auto-Eval modules: {e}")

# ------------------------------------------------------------
# Router initialization
# ------------------------------------------------------------
router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
)

logger = logging.getLogger("evaluation")

# ------------------------------------------------------------
# Evaluate user answers endpoint
# ------------------------------------------------------------
@router.post("/evaluate-answers")
async def evaluate_answers(user_name: str, topic: str, db: Session = Depends(get_db)):
    """
    Evaluate all answers for a given user and topic using the Auto-Eval MCP pipeline.
    This performs: Retriever → ModelGenerator → RubricGenerator → Evaluator → Reflector → Aggregator
    """
    answers = db.query(models.TestAnswer).filter_by(user_name=user_name, topic=topic).all()
    if not answers:
        raise HTTPException(status_code=404, detail="No answers found for this user/topic.")

    try:
        retriever = RetrieverAgent()
        model_gen = ModelGeneratorAgent()
        rubric_gen = RubricGeneratorAgent()
        evaluator = EvaluatorAgent()
        reflector = ReflectorAgent()
        aggregator = Aggregator()
        graph = build_graph()

        results = []
        for ans in answers:
            inp = PipelineInput(question=ans.question, student_answer=ans.answer, top_k=3)
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

            # Run full pipeline graph
            output = graph.invoke(state)
            result_data = output["result"].model_dump()

            results.append({
                "question": ans.question,
                "answer": ans.answer,
                "score": result_data.get("grade", 0),
                "feedback": result_data.get("feedback", ""),
                "confidence": result_data.get("confidence", 0.0),
            })

        avg_score = sum(r["score"] for r in results) / len(results)

        return {
            "user_name": user_name,
            "topic": topic,
            "results": results,
            "average_score": round(avg_score, 2),
        }

    except Exception as e:
        logger.exception("❌ Auto-Eval MCP pipeline failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

# ------------------------------------------------------------
# Optional: simple health check route for the MCP evaluator
# ------------------------------------------------------------
@router.get("/status")
async def evaluation_status():
    """Quick health check for the evaluation service."""
    return {"status": "ok", "message": "Auto-Eval MCP pipeline is operational."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("routes.evaluation:router", host="127.0.0.1", port=8002, reload=True)