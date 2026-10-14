"""
GeneratedSimulation schema.

Represents the structured output of a single generator call.
The generator is responsible for producing a schema-valid instance of this
model on every call (with JSON-repair retry if needed — Phase 2).

Source of truth: authoritative field definitions (v2 correction, 2026-08-27).
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class GeneratedSimulation(BaseModel):
    """
    The output of one generator call for a given ScenarioSpecification.

    All fields are required. The generator must populate every field;
    revision_instructions used as generator *input* are carried in loop state,
    not stored here.
    """

    # ------------------------------------------------------------------
    # Identity / provenance
    # ------------------------------------------------------------------

    generation_id: str = Field(
        ...,
        description="UUID identifying this specific generation call.",
    )

    scenario_id: str = Field(
        ...,
        description="UUID of the ScenarioSpecification that was used to generate this.",
    )

    # ------------------------------------------------------------------
    # Email / message content
    # ------------------------------------------------------------------

    subject: str = Field(
        ...,
        description="Email subject line of the simulated phishing message.",
    )

    sender: str = Field(
        ...,
        description=(
            "Apparent sender string (e.g. 'Finance Team <ap@accts-training.example>'). "
            "Must be plausible but must not use a real brand name or domain."
        ),
    )

    body: str = Field(
        ...,
        description=(
            "Full body text of the simulated phishing email, "
            "formatted as plain text."
        ),
    )

    # ------------------------------------------------------------------
    # Structural / metadata fields
    # ------------------------------------------------------------------

    metadata: dict = Field(
        default_factory=dict,
        description=(
            "Arbitrary generator-produced metadata "
            "(e.g. tone notes, generation rationale, difficulty justification). "
            "Consumed by the verifier and logged in the run record."
        ),
    )

    intended_indicators: list[str] = Field(
        ...,
        description=(
            "List of phishing indicators the generator claims to have embedded. "
            "The verifier checks these against the specification's desired_indicators."
        ),
    )

    # ------------------------------------------------------------------
    # Provenance / reproducibility
    # ------------------------------------------------------------------

    model: str = Field(
        ...,
        description="Name of the LLM model that produced this generation.",
    )

    prompt_version: str = Field(
        ...,
        description="Version identifier of the generator prompt template used.",
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when this generation was produced.",
    )
