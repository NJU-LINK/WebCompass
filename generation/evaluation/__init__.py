"""
WebCompass Evaluation Module

Provides tools for evaluating generated websites across three dimensions:
- Runnability: Page loads without errors
- Spec Implementation: Interactions work correctly
- Design Quality: Visual fidelity to reference
"""

from .evaluate import (
    evaluate_modality,
    score_task_from_checklist,
    TaskScore,
    EvalSummary,
)

__all__ = [
    "evaluate_modality",
    "score_task_from_checklist",
    "TaskScore",
    "EvalSummary",
]
