import typer
from rich import print
import logging
from typing import Dict, Any

from ..core.types import PipelineInput
from ..agents.retriever import RetrieverAgent
from ..agents.model_generator import ModelGeneratorAgent
from ..agents.rubric_generator import RubricGeneratorAgent
from ..agents.evaluator import EvaluatorAgent
from ..agents.reflector import ReflectorAgent
from ..agents.aggregator import Aggregator
from .graph import build_graph

# Typer CLI setup
app = typer.Typer(help="Auto-Eval CLI - Run agentic grading and feedback generation.")

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


@app.command()
def run(
    question: str = typer.Option(..., help="The question text."),
    student_answer: str = typer.Option(
        ..., "--answer", "--student-answer", help="The student's answer text."
    ),
    top_k: int = typer.Option(5, help="Number of top passages to retrieve."),
    use_graph: bool = typer.Option(False, help="Use graph-based multi-agent pipeline."),
):
    """
    Run Auto-Eval pipeline via command line.
    Example:
      python -m auto_eval.pipeline.cli --question "..." --answer "..." --top-k 3
    """
    try:
        inp = PipelineInput(question=question, student_answer=student_answer, top_k=top_k)

        # Initialize agents
        retriever = RetrieverAgent()
        model_gen = ModelGeneratorAgent()
        rubric_gen = RubricGeneratorAgent()
        evaluator = EvaluatorAgent()
        reflector = ReflectorAgent()
        aggregator = Aggregator()

        # ----------------------------------------------------------------------
        # GRAPH-BASED MULTI-AGENT PIPELINE
        # ----------------------------------------------------------------------
        if use_graph:
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
            print(out["result"].model_dump())
            return

        # ----------------------------------------------------------------------
        # STANDARD SEQUENTIAL PIPELINE
        # ----------------------------------------------------------------------
        logger.info("🔍 Retrieving top passages...")
        retrieved = retriever.retrieve(inp.question, inp.top_k)
        passages_text = "\n".join(p.text for p in retrieved.passages)

        logger.info("🧠 Generating model answer and rubric...")
        model_answer = model_gen.generate(inp.question, inp.student_answer, passages_text)
        rubric = rubric_gen.finalize(model_answer.candidate_rubric)

        logger.info("📊 Evaluating student answer...")
        evaluation = evaluator.evaluate(
            inp.question,
            inp.student_answer,
            model_answer.answer,
            rubric.rubric_text,
            passages_text,
        )

        logger.info("🪞 Reflecting and refining confidence...")
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

        print(result.model_dump())

    except Exception as e:
        logger.exception("❌ Auto-Eval pipeline failed: %s", e)
        typer.echo(f"[red]Pipeline error: {e}[/red]", err=True)


# ----------------------------------------------------------------------
# ✅ New: programmatic helper for FastAPI / backend integration
# ----------------------------------------------------------------------
def run_pipeline_cli(
    question: str, answer: str, top_k: int = 3, use_graph: bool = False
) -> Dict[str, Any]:
    """
    Internal callable wrapper around the CLI pipeline.
    Allows Auto-Eval to be invoked programmatically (e.g., from FastAPI).
    Returns a dict containing grade, feedback, rubric, confidence, etc.
    """
    try:
        inp = PipelineInput(question=question, student_answer=answer, top_k=top_k)

        # Initialize agents
        retriever = RetrieverAgent()
        model_gen = ModelGeneratorAgent()
        rubric_gen = RubricGeneratorAgent()
        evaluator = EvaluatorAgent()
        reflector = ReflectorAgent()
        aggregator = Aggregator()

        # Optional graph-based version
        if use_graph:
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

        # Sequential pipeline (same as CLI)
        retrieved = retriever.retrieve(inp.question, inp.top_k)
        passages_text = "\n".join(p.text for p in retrieved.passages)

        model_answer = model_gen.generate(inp.question, inp.student_answer, passages_text)
        rubric = rubric_gen.finalize(model_answer.candidate_rubric)
        evaluation = evaluator.evaluate(
            inp.question,
            inp.student_answer,
            model_answer.answer,
            rubric.rubric_text,
            passages_text,
        )
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

    except Exception as e:
        logger.exception("❌ Auto-Eval programmatic pipeline failed: %s", e)
        return {
            "grade": 0.0,
            "feedback": f"Pipeline error: {e}",
            "confidence": 0.0,
            "rubric": "",
            "model_answer": "",
            "provenance_ids": [],
        }


if __name__ == "__main__":
    app()
