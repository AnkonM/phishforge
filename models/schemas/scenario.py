"""
ScenarioSpecification schema.

Represents the user-supplied input to a PhishForge run, either constructed
from CLI flags or loaded from a JSON file via --input.

Source of truth: authoritative field definitions (v2 correction, 2026-08-27).
"""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Supported enumerations (kept in sync with config.py)
# ---------------------------------------------------------------------------

TargetRole = Literal[
    "finance",
    "hr",
    "it",
    "sales",
    "operations",
    "executive",
]


class ScenarioSpecification(BaseModel):
    """
    The complete, validated description of a phishing-awareness scenario.

    All fields are required unless a default is stated.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    scenario_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID uniquely identifying this scenario specification.",
    )

    # ------------------------------------------------------------------
    # Required content fields
    # ------------------------------------------------------------------

    organization_context: str = Field(
        ...,
        description=(
            "Free-text description of the organisation, team size, tools used, "
            "and any other context that should shape the simulation."
        ),
    )

    target_role: TargetRole = Field(
        ...,
        description=(
            "Target employee role — constrains which workflow details and "
            "authority figures are plausible in the scenario."
        ),
    )

    scenario_type: str = Field(
        ...,
        description=(
            "Category of phishing attack being simulated "
            "(e.g. 'invoice_fraud', 'password_alert', 'hr_document_request', "
            "'delivery_expense_notification', 'account_verification', "
            "'internal_policy_update')."
        ),
    )

    difficulty: Literal[1, 2, 3, 4] = Field(
        ...,
        description=(
            "Difficulty level on a 1–4 scale. "
            "1 = obvious tells, easily spotted; "
            "4 = highly convincing, very subtle indicators."
        ),
    )

    language: str = Field(
        default="en",
        description="ISO 639-1 language code for the generated content.",
    )

    desired_indicators: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Ordered list of phishing indicators the generator must embed "
            "(e.g. 'urgency', 'authority_impersonation', 'suspicious_link')."
        ),
    )

    # ------------------------------------------------------------------
    # Optional / defaulted fields
    # ------------------------------------------------------------------

    prohibited_elements: list[str] = Field(
        default_factory=list,
        description=(
            "Elements the generator must NOT include "
            "(e.g. 'real brand names', 'credential harvesting links')."
        ),
    )

    simulation_constraints: dict = Field(
        default_factory=dict,
        description=(
            "Arbitrary key-value pairs for additional generation constraints "
            "(e.g. {\"max_body_words\": 200, \"tone\": \"formal\"})."
        ),
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("desired_indicators")
    @classmethod
    def indicators_must_be_non_empty_strings(cls, v: list[str]) -> list[str]:
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Each indicator must be a non-empty string.")
        return [item.strip() for item in v]

    @field_validator("language")
    @classmethod
    def language_must_be_two_letter_code(cls, v: str) -> str:
        if not (v.isalpha() and len(v) == 2):
            raise ValueError(
                f"language must be a two-letter ISO 639-1 code, got '{v}'."
            )
        return v.lower()
