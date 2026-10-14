"""
core/scoring/scoring_engine.py

Deterministic Scoring Engine for PhishForge.
Computes overall quality score Q and classifies into PASS / REVISE / FAIL bands.

Source of truth: Document B v2 §13.

Weighted formula (Option A - 5 verified quality dimensions summing to 1.0):
  Q = w_realism * realism_score
    + w_relevance * relevance_score
    + w_indicators * indicator_score
    + w_difficulty * difficulty_score
    + w_language * language_score

Band classification:
  Q >= 80.0            -> PASS
  60.0 <= Q < 80.0     -> REVISE
  Q < 60.0             -> FAIL

IMPORTANT ARCHITECTURAL INVARIANT:
Safety evaluation (Phase 3 Safety Gate) is a strict, prior gate. A safety failure
aborts generation immediately into terminal state REJECTED_UNSAFE in the Phase 6
Orchestration layer. Scoring Engine evaluates quality dimensions ONLY for artifacts
that have already cleared safety.

Zero LLM calls, zero I/O — pure deterministic computation.
"""

from __future__ import annotations

from typing import Literal

import config
from models.schemas.verification import VerificationResult


def classify_band(score: float) -> Literal["PASS", "REVISE", "FAIL"]:
    """
    Classify a numerical score (0–100) into PASS / REVISE / FAIL bands.

    Thresholds:
      score >= config.PASS_THRESHOLD (80)   -> PASS
      score >= config.REVISE_THRESHOLD (60) -> REVISE
      score < config.REVISE_THRESHOLD       -> FAIL
    """
    if score >= config.PASS_THRESHOLD:
        return config.BAND_PASS
    if score >= config.REVISE_THRESHOLD:
        return config.BAND_REVISE
    return config.BAND_FAIL


def compute(verification: VerificationResult) -> VerificationResult:
    """
    Compute overall weighted score and assign pass_fail classification band.

    Parameters
    ----------
    verification:
        VerificationResult with individual dimension scores populated.

    Returns
    -------
    VerificationResult
        Updated VerificationResult with computed overall_score and pass_fail.
    """
    weights = config.SCORING_WEIGHTS

    raw_score = (
        verification.realism_score * weights["realism"]
        + verification.relevance_score * weights["role_relevance"]
        + verification.indicator_score * weights["indicator_coverage"]
        + verification.difficulty_score * weights["difficulty_match"]
        + verification.language_score * weights["language_quality"]
    )

    # Round to 1 decimal place for clean, stable reporting
    overall_score = round(max(0.0, min(100.0, raw_score)), 1)
    pass_fail = classify_band(overall_score)

    return verification.model_copy(
        update={
            "overall_score": overall_score,
            "pass_fail": pass_fail,
        }
    )


# Alias for intuitive caller ergonomics
compute_score = compute
