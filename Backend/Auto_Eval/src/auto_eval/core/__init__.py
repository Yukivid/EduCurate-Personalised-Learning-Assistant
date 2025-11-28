"""
Core types and configuration for Auto-Eval.
"""

from .config import ENV, Env
from .types import (
    Passage,
    RetrievalResult,
    ModelAnswer,
    Rubric,
    Evaluation,
    Reflection,
    AggregatedResult,
    PipelineInput,
    Settings,
)

__all__ = [
    "ENV",
    "Env",
    "Passage",
    "RetrievalResult",
    "ModelAnswer",
    "Rubric",
    "Evaluation",
    "Reflection",
    "AggregatedResult",
    "PipelineInput",
    "Settings",
]