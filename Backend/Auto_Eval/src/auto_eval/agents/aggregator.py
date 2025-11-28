from ..core.types import AggregatedResult

class Aggregator:
    def __init__(self):
        pass

    def aggregate(self, score: float, feedback: str, model_answer: str, rubric_text: str, provenance_ids: list, confidence: float) -> AggregatedResult:
        return AggregatedResult(
            grade=score,
            feedback=feedback,
            provenance_ids=provenance_ids,
            confidence=confidence,
            model_answer=model_answer,
            rubric=rubric_text,
        )
