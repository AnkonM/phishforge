"""
RefinementResult schema.

Represents the Refinement Controller's assessment after one loop iteration:
what was weak, what the next generation should fix, and whether the loop
should continue or terminate.

Source of truth: authoritative field definitions (v2 correction, 2026-08-27).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# Termination reason values — map to the loop's terminal states.
TerminationReason = Literal[
    "PASS",
    "MAX_ITERATIONS",
    "NO_IMPROVEMENT",
    "SAFETY_FAIL",
]


class RefinementResult(BaseModel):
    """
    Per-iteration output of the Refinement Controller.

    Stored in the RunRecord's iteration history; the Refinement Controller
    reads score history to detect no-improvement early stopping.
    """

    iteration_number: int = Field(
        ...,
        ge=1,
        description="1-indexed iteration number this result belongs to.",
    )

    prior_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description=(
            "Overall score from the previous iteration, or None for iteration 1 "
            "(no prior score exists)."
        ),
    )

    weaknesses: list[str] = Field(
        default_factory=list,
        description=(
            "Actionable weakness strings sourced from the VerificationResult's "
            "semantic_findings — the concrete problems to fix in the next iteration."
        ),
    )

    revision_instructions: str = Field(
        ...,
        description=(
            "Structured critique to feed into the next generator call. "
            "Always present: even for terminal iterations this records what "
            "the controller would have said next."
        ),
    )

    new_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description=(
            "Overall score from this iteration's verification result, or None "
            "if the iteration was rejected by the safety gate before scoring."
        ),
    )

    score_delta: float | None = Field(
        default=None,
        description=(
            "new_score - prior_score, or None if either score is unavailable. "
            "Used by the no-improvement early-stopping check."
        ),
    )

    termination_reason: TerminationReason | None = Field(
        default=None,
        description=(
            "Why the loop stopped after this iteration, or None if the loop "
            "continues (i.e., another REVISE iteration follows). "
            "PASS = score crossed threshold; MAX_ITERATIONS = budget exhausted; "
            "NO_IMPROVEMENT = epsilon/patience triggered; "
            "SAFETY_FAIL = safety gate rejected this iteration."
        ),
    )
