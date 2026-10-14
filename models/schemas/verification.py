"""
VerificationResult schema.

Represents the combined output of the Hybrid Verifier: Layer A deterministic
checks and Layer B LLM semantic judge, flattened into a single typed result.

Layer A produces indicator_score and language_score (rule-based, deterministic).
Layer B produces realism_score, relevance_score, difficulty_score (LLM-judged).
safety_status is the output of the Safety Gate and is carried here for record-keeping.

Source of truth: authoritative field definitions (v2 correction, 2026-08-27).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class VerificationResult(BaseModel):
    """
    Combined output of the Hybrid Verifier for one generator iteration.

    The Scoring Engine reads the five *_score fields to compute the
    weighted overall_score and classify it into pass_fail.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    verification_id: str = Field(
        ...,
        description="UUID identifying this verification result.",
    )

    generation_id: str = Field(
        ...,
        description="UUID of the GeneratedSimulation that was verified.",
    )

    # ------------------------------------------------------------------
    # Layer B — LLM semantic scores
    # ------------------------------------------------------------------

    realism_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description=(
            "LLM-judged score (0–100): how realistic and believable "
            "the simulated email is."
        ),
    )

    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description=(
            "LLM-judged score (0–100): how well the content matches "
            "the target role's typical workflows and vocabulary."
        ),
    )

    difficulty_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description=(
            "LLM-judged score (0–100): calibration accuracy — how closely "
            "the content's sophistication matches the requested difficulty level."
        ),
    )

    # ------------------------------------------------------------------
    # Layer A — deterministic rule-based scores
    # ------------------------------------------------------------------

    indicator_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description=(
            "Rule-based score (0–100): degree to which all requested "
            "phishing indicators are present and correctly embedded."
        ),
    )

    language_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description=(
            "Rule-based score (0–100): grammar, fluency, and language quality "
            "appropriate to the requested language and role."
        ),
    )

    # ------------------------------------------------------------------
    # Safety gate result (carried for audit / record-keeping)
    # ------------------------------------------------------------------

    safety_status: Literal["PASS", "FAIL"] = Field(
        ...,
        description=(
            "Safety gate result. FAIL is a hard reject — the run terminates "
            "as REJECTED_UNSAFE regardless of quality scores."
        ),
    )

    safety_findings: list[str] = Field(
        default_factory=list,
        description=(
            "Safety gate violation descriptions. "
            "Empty iff safety_status == 'PASS'."
        ),
    )

    # ------------------------------------------------------------------
    # Semantic findings (from Layer B)
    # ------------------------------------------------------------------

    semantic_findings: list[str] = Field(
        default_factory=list,
        description=(
            "Actionable weakness strings from the LLM judge — "
            "fed into revision_instructions by the Refinement Controller."
        ),
    )

    # ------------------------------------------------------------------
    # Computed summary fields (set by the Scoring Engine)
    # ------------------------------------------------------------------

    overall_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Weighted average of all five dimension scores, 0–100.",
    )

    pass_fail: Literal["PASS", "REVISE", "FAIL"] = Field(
        ...,
        description=(
            "Score band: PASS (>= PASS_THRESHOLD), "
            "REVISE (>= REVISE_THRESHOLD), "
            "FAIL (< REVISE_THRESHOLD). Thresholds defined in config.py."
        ),
    )

    verifier_version: str = Field(
        ...,
        description="Version identifier of the verifier prompt / rule-set used.",
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("semantic_findings", mode="before")
    @classmethod
    def deduplicate_findings(cls, v: list[str]) -> list[str]:
        """Remove exact duplicates while preserving insertion order."""
        seen: set[str] = set()
        deduped = []
        for item in v:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped
