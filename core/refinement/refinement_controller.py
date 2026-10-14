"""
core/refinement/refinement_controller.py

Refinement Controller for PhishForge.

Translates VerificationResult weaknesses and semantic findings into
imperative, structured revision instructions for subsequent generator iterations,
and determines early-stopping conditions based on score progression.

Source of truth: Document B v2 §15.

Architecture rules (Document B v2 §7):
  - No print() statements.
  - No CLI-specific logic.
  - Pure functions, zero external I/O, zero LLM calls.
"""

from __future__ import annotations

import config
from models.schemas.refinement import RefinementResult, TerminationReason
from models.schemas.verification import VerificationResult


def build_instructions(verification: VerificationResult) -> str:
    """
    Convert verification findings into structured, imperative revision instructions.

    Parameters
    ----------
    verification:
        The scored VerificationResult from the current iteration.

    Returns
    -------
    str
        Structured critique instructions for the generator.
    """
    findings = verification.semantic_findings
    if not findings:
        return (
            "Maintain current simulation realism and role relevance. "
            "Ensure all scenario indicators and safety constraints are fully preserved."
        )

    lines = [
        "Please address the following specific weaknesses identified in the previous generation:"
    ]
    for idx, finding in enumerate(findings, 1):
        lines.append(f"{idx}. {finding.strip()}")

    lines.append(
        "\nPreserve the scenario intent (target role, organization context, difficulty target) "
        "and address ONLY the listed weaknesses above. Do not introduce real company names or real URLs."
    )

    return "\n".join(lines)


def should_stop_early(
    score_history: list[float],
    patience: int | None = None,
    epsilon: float | None = None,
) -> bool:
    """
    Determine whether the refinement loop should terminate early due to score plateauing.

    Checks if the score improvement over the last `patience` consecutive transitions
    has remained strictly below `epsilon`.

    Parameters
    ----------
    score_history:
        Ordered list of overall quality scores Q from consecutive iterations.
    patience:
        Number of consecutive non-improving steps to check (defaults to config.IMPROVEMENT_PATIENCE).
    epsilon:
        Minimum required improvement threshold (defaults to config.IMPROVEMENT_EPSILON).

    Returns
    -------
    bool
        True if the loop has stalled and should stop early, False otherwise.
    """
    if patience is None:
        patience = config.IMPROVEMENT_PATIENCE
    if epsilon is None:
        epsilon = config.IMPROVEMENT_EPSILON

    # Need at least (patience + 1) scores to evaluate `patience` transitions
    if len(score_history) < patience + 1:
        return False

    # Check the last `patience` deltas
    recent_deltas = [
        score_history[i] - score_history[i - 1]
        for i in range(len(score_history) - patience, len(score_history))
    ]

    # Stalled if every recent delta is less than epsilon
    return all(delta < epsilon for delta in recent_deltas)


def create_refinement_result(
    iteration_number: int,
    verification: VerificationResult | None,
    prior_score: float | None,
    termination_reason: TerminationReason | None = None,
) -> RefinementResult:
    """
    Construct a validated RefinementResult model for recording in the iteration history.
    """
    weaknesses = verification.semantic_findings if verification else []
    revision_instructions = (
        build_instructions(verification)
        if verification
        else "Generation or safety check failed; no revision instructions available."
    )
    new_score = verification.overall_score if verification else None
    score_delta = (
        round(new_score - prior_score, 1)
        if (new_score is not None and prior_score is not None)
        else None
    )

    return RefinementResult(
        iteration_number=iteration_number,
        prior_score=prior_score,
        weaknesses=weaknesses,
        revision_instructions=revision_instructions,
        new_score=new_score,
        score_delta=score_delta,
        termination_reason=termination_reason,
    )
