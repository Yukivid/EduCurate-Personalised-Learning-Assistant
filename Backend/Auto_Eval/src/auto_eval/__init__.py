"""
Auto-Eval: Multi-agent automated evaluation system.
"""

__version__ = "0.1.0"

from .core.config import ENV
from .core.types import (
    Passage,
    RetrievalResult,
    ModelAnswer,
    Rubric,
    Evaluation,
    Reflection,
    AggregatedResult,
    PipelineInput,
)

__all__ = [
    "ENV",
    "Passage",
    "RetrievalResult",
    "ModelAnswer",
    "Rubric",
    "Evaluation",
    "Reflection",
    "AggregatedResult",
    "PipelineInput",
]