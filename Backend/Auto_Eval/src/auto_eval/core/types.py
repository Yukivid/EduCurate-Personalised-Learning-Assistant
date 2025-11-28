from pydantic import BaseModel, Field
from typing import List, Optional, Any

class Passage(BaseModel):
    id: str
    text: str
    metadata: dict = Field(default_factory=dict)

class RetrievalResult(BaseModel):
    query: str
    passages: List[Passage]

class ModelAnswer(BaseModel):
    answer: str
    candidate_rubric: str
    reasoning: Optional[str] = None

class Rubric(BaseModel):
    rubric_text: str
    criteria: List[str] = Field(default_factory=list)

class Evaluation(BaseModel):
    score: float
    feedback: str
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None

class Reflection(BaseModel):
    issues: List[str] = Field(default_factory=list)
    adjustments: Optional[str] = None
    confidence_adjustment: Optional[float] = None

class AggregatedResult(BaseModel):
    grade: float
    feedback: str
    provenance_ids: List[str]
    confidence: float
    model_answer: str
    rubric: str

class PipelineInput(BaseModel):
    question: str
    student_answer: str
    top_k: int = 5

class Settings(BaseModel):
    vector_store: str = "faiss"  # or "chroma"
    embedding_model: str = "openai"
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.0

__all__ = [
    "Passage", "RetrievalResult", "ModelAnswer", "Rubric", "Evaluation", "Reflection", "AggregatedResult", "PipelineInput", "Settings",
]
