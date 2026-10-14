"""
core/verification/llm_judge.py

Layer B of the Hybrid Verifier: LLM-based semantic judge.
Evaluates realism, role relevance, difficulty calibration, and actionable findings.

Calls the Gemini API via core.generation.llm_client.call_llm(),
at VERIFIER_TEMPERATURE (0.2).

Includes one JSON-repair retry; raises VerificationFailure on repeated failure.

Source of truth: Document B v2 §12.
"""

from __future__ import annotations

import json
from pathlib import Path
from string import Template
from typing import Any

from pydantic import BaseModel, Field

import config
from core.generation.llm_client import call_llm
from models.schemas.scenario import ScenarioSpecification
from models.schemas.simulation import GeneratedSimulation

# ---------------------------------------------------------------------------
# Constants & Template
# ---------------------------------------------------------------------------

PROMPT_VERSION = "v1"

_PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts" / "verifier"
_PROMPT_FILE = _PROMPT_DIR / f"{PROMPT_VERSION}_verifier.txt"

_REPAIR_PROMPT = (
    "Your previous response was not valid JSON matching the required verifier schema. "
    "Return ONLY a valid JSON object with exactly these fields: "
    "realism_score (0-100), relevance_score (0-100), difficulty_score (0-100), "
    "assessed_difficulty (1-4), difficulty_rationale (string), semantic_findings (list of strings)."
)


# ---------------------------------------------------------------------------
# Public Exception & Result Model
# ---------------------------------------------------------------------------


class VerificationFailure(Exception):
    """
    Raised when the verifier cannot obtain a schema-valid response from the LLM
    after exhausting its retry budget.
    """

    def __init__(self, reason: str, raw_response: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.raw_response = raw_response


class LayerBResult(BaseModel):
    """Output of Layer B semantic evaluation."""

    realism_score: float = Field(..., ge=0.0, le=100.0)
    relevance_score: float = Field(..., ge=0.0, le=100.0)
    difficulty_score: float = Field(..., ge=0.0, le=100.0)
    assessed_difficulty: int = Field(default=1, ge=1, le=4)
    difficulty_rationale: str = Field(default="")
    semantic_findings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Prompt Construction
# ---------------------------------------------------------------------------


def _load_template() -> str:
    """Read the verifier prompt template file."""
    if not _PROMPT_FILE.exists():
        raise FileNotFoundError(f"Verifier prompt template not found: {_PROMPT_FILE}")
    return _PROMPT_FILE.read_text(encoding="utf-8")


def build_verifier_prompt(
    spec: ScenarioSpecification,
    sim: GeneratedSimulation,
) -> str:
    """Build the prompt string for the LLM judge."""
    template = _load_template()

    desired_indicators_str = (
        ", ".join(spec.desired_indicators) if spec.desired_indicators else "none specified"
    )
    prohibited_elements_str = (
        ", ".join(spec.prohibited_elements) if spec.prohibited_elements else "none"
    )
    simulation_constraints_str = (
        json.dumps(spec.simulation_constraints, ensure_ascii=False)
        if spec.simulation_constraints
        else "none"
    )
    intended_indicators_str = (
        ", ".join(sim.intended_indicators) if sim.intended_indicators else "none specified"
    )
    metadata_str = (
        json.dumps(sim.metadata, ensure_ascii=False) if sim.metadata else "none"
    )

    return Template(template).safe_substitute(
        organization_context=spec.organization_context,
        target_role=spec.target_role,
        scenario_type=spec.scenario_type,
        difficulty=spec.difficulty,
        language=spec.language,
        desired_indicators=desired_indicators_str,
        prohibited_elements=prohibited_elements_str,
        simulation_constraints=simulation_constraints_str,
        simulation_subject=sim.subject,
        simulation_sender=sim.sender,
        simulation_body=sim.body,
        simulation_intended_indicators=intended_indicators_str,
        simulation_metadata=metadata_str,
    )


# ---------------------------------------------------------------------------
# Response Parsing & Execution
# ---------------------------------------------------------------------------


def _parse_and_validate_layer_b(raw: str) -> LayerBResult:
    """Parse and validate JSON response from the LLM judge."""
    raw = raw.strip()
    if raw.startswith("```"):
        raise ValueError("Response was wrapped in a markdown code fence.")

    data = json.loads(raw)

    # Ensure scores are floats and properly constrained
    return LayerBResult(
        realism_score=float(data.get("realism_score", 0.0)),
        relevance_score=float(data.get("relevance_score", 0.0)),
        difficulty_score=float(data.get("difficulty_score", 0.0)),
        assessed_difficulty=int(data.get("assessed_difficulty", 1)),
        difficulty_rationale=str(data.get("difficulty_rationale", "")),
        semantic_findings=list(data.get("semantic_findings", [])),
    )


def run_llm_judge(
    spec: ScenarioSpecification,
    sim: GeneratedSimulation,
    *,
    _client: Any = None,
) -> LayerBResult:
    """
    Run Layer B semantic judge on the simulation.

    Parameters
    ----------
    spec:
        Target scenario specification.
    sim:
        Generated simulation under evaluation.
    _client:
        Optional injected Gemini client or mock.

    Returns
    -------
    LayerBResult
        Validated realism_score, relevance_score, difficulty_score, and semantic_findings.

    Raises
    ------
    VerificationFailure
        If the judge fails to return a valid JSON structure after the repair retry.
    """
    prompt = build_verifier_prompt(spec, sim)

    # First attempt
    try:
        raw_first = call_llm(
            prompt,
            temperature=config.VERIFIER_TEMPERATURE,
            max_tokens=config.VERIFIER_MAX_TOKENS,
            _client=_client,
        )
        return _parse_and_validate_layer_b(raw_first)
    except Exception:
        pass  # Fall through to retry

    # Repair retry
    repair_prompt = prompt + "\n\n" + _REPAIR_PROMPT
    try:
        raw_retry = call_llm(
            repair_prompt,
            temperature=config.VERIFIER_TEMPERATURE,
            max_tokens=config.VERIFIER_MAX_TOKENS,
            _client=_client,
        )
        return _parse_and_validate_layer_b(raw_retry)
    except Exception as retry_err:
        raise VerificationFailure(
            f"Verifier Layer B failed to return valid JSON after repair retry. Last error: {retry_err}"
        ) from retry_err
