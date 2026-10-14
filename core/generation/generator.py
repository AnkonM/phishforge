"""
core/generation/generator.py

Implements `generate()` -- the single public function of this module.
Calls the Gemini API via llm_client.call_llm(), parses the JSON response,
validates it against GeneratedSimulation, and fills in provenance fields
(generation_id, scenario_id, model, prompt_version, timestamp) in code.

One JSON-repair retry is implemented: if the first response is not valid
JSON or does not validate, the model is re-prompted once with correction
instructions. If the retry also fails, GenerationFailure is raised.

Architecture rules (Document B v2 SS7):
  - No print() statements.
  - No CLI-specific logic.
  - Raise exceptions; let the orchestration/CLI layer handle presentation.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

import config
from core.generation.llm_client import call_llm
from core.generation.prompt_builder import PROMPT_VERSION, build_prompt
from models.schemas.scenario import ScenarioSpecification
from models.schemas.simulation import GeneratedSimulation

# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------


class GenerationFailure(Exception):
    """
    Raised when the generator cannot produce a schema-valid GeneratedSimulation
    after exhausting its retry budget.

    Attributes
    ----------
    reason : str
        Human-readable description of what failed.
    raw_response : str | None
        The last raw LLM response text, if any was received.
    """

    def __init__(self, reason: str, raw_response: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.raw_response = raw_response


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_REPAIR_PROMPT = (
    "Your previous response was not valid JSON matching the required schema. "
    "Return ONLY a valid JSON object -- no markdown fences, no prose -- "
    "with exactly these five fields: subject, sender, body, intended_indicators, metadata."
)


def _parse_and_validate(
    raw: str,
    spec: ScenarioSpecification,
) -> GeneratedSimulation:
    """
    Parse `raw` as JSON and validate against GeneratedSimulation.

    Fills in provenance fields NOT requested from the LLM:
      generation_id, scenario_id, model, prompt_version, timestamp.

    Raises
    ------
    ValueError / json.JSONDecodeError
        If JSON parsing fails.
    pydantic.ValidationError
        If the parsed dict does not match GeneratedSimulation.
    """
    # Strip leading/trailing whitespace; Gemini sometimes adds a newline.
    raw = raw.strip()

    # If the model wrapped the JSON in a markdown fence despite instructions,
    # strip the fence so the repair retry sees a clean parse failure instead
    # of silently accepting malformed output.
    # NOTE: we do NOT silently accept fenced output -- the fence means the
    # model ignored the formatting instruction, which is itself a failure that
    # should trigger the repair retry or raise GenerationFailure.
    if raw.startswith("```"):
        # Raise immediately so the repair retry fires with the fence-removal prompt.
        raise ValueError("Response was wrapped in a markdown code fence.")

    data = json.loads(raw)  # raises json.JSONDecodeError on bad JSON

    # Inject provenance fields -- the LLM is never asked to produce these.
    data["generation_id"] = str(uuid.uuid4())
    data["scenario_id"] = spec.scenario_id
    data["model"] = config.MODEL_NAME
    data["prompt_version"] = PROMPT_VERSION
    data["timestamp"] = datetime.now(timezone.utc)

    return GeneratedSimulation(**data)  # raises pydantic.ValidationError on bad shape


def _do_call(
    prompt: str,
    _client=None,
) -> str:
    """Thin wrapper that passes through the optional mock client."""
    return call_llm(
        prompt,
        temperature=config.GENERATOR_TEMPERATURE,
        max_tokens=config.GENERATOR_MAX_TOKENS,
        _client=_client,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate(
    spec: ScenarioSpecification,
    revision_instructions: str | None = None,
    *,
    _client=None,
) -> GeneratedSimulation:
    """
    Generate a phishing-awareness training simulation for the given scenario.

    Parameters
    ----------
    spec:
        Validated scenario specification.
    revision_instructions:
        Optional critique from the Refinement Controller. When provided, the
        prompt instructs the model to preserve scenario intent and address only
        the listed weaknesses (anti-drift).
    _client:
        Optional pre-constructed Gemini client -- injected by tests.
        If None and GEMINI_API_KEY is unset, raises GenerationFailure.

    Returns
    -------
    GeneratedSimulation
        A validated simulation with all provenance fields populated.

    Raises
    ------
    GenerationFailure
        If the LLM produces invalid JSON/schema on both the initial call and
        the repair retry, or if GEMINI_API_KEY is not set.
    """
    api_key = config.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    if _client is None and not api_key:
        raise GenerationFailure(
            "GEMINI_API_KEY is not set. "
            "Copy .env.example to .env and set your Gemini API key."
        )

    prompt = build_prompt(spec, revision_instructions=revision_instructions)

    # First attempt
    raw_first = _do_call(prompt, _client=_client)

    try:
        return _parse_and_validate(raw_first, spec)
    except Exception:
        pass  # fall through to repair retry

    # Repair retry -- give the model explicit correction instructions.
    repair_prompt = prompt + "\n\n" + _REPAIR_PROMPT
    raw_retry = _do_call(repair_prompt, _client=_client)

    try:
        return _parse_and_validate(raw_retry, spec)
    except Exception as retry_err:
        raise GenerationFailure(
            f"Generator failed to produce valid JSON after repair retry. "
            f"Last error: {retry_err}",
            raw_response=raw_retry,
        ) from retry_err
