"""
core/generation/prompt_builder.py

Loads the generator prompt template and fills it with values from a
ScenarioSpecification (and optional revision_instructions).

Kept separate from generator.py so prompt construction is unit-testable
without any API calls -- Document B v2 SS7 / SS26 principle.

No print statements, no I/O side effects.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from string import Template

from models.schemas.scenario import ScenarioSpecification

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROMPT_VERSION = "v1"

_PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts" / "generator"
_PROMPT_FILE = _PROMPT_DIR / f"{PROMPT_VERSION}_generator.txt"

# Revision block template — injected when revision_instructions are provided.
_REVISION_BLOCK_TEMPLATE = """\
=== REVISION INSTRUCTIONS ===
A previous generation of this scenario was evaluated and found to be insufficient.
You MUST preserve the original scenario intent exactly:
  - Keep the same target role, organisation context, scenario type, and difficulty level.
  - Do NOT change the overall scenario framing or introduce new scenario elements.

Address ONLY the specific weaknesses listed below. Do not make changes unrelated to these findings:

$revision_instructions

Your revised output must still comply with all safety constraints above and return the same JSON structure."""


def _load_template() -> str:
    """Read the prompt template file. Raises FileNotFoundError if missing."""
    if not _PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"Generator prompt template not found: {_PROMPT_FILE}"
        )
    return _PROMPT_FILE.read_text(encoding="utf-8")


def build_prompt(
    spec: ScenarioSpecification,
    revision_instructions: str | None = None,
) -> str:
    """
    Build the final generator prompt string from a ScenarioSpecification.

    Parameters
    ----------
    spec:
        The validated scenario specification describing what to generate.
    revision_instructions:
        Optional critique from the Refinement Controller. When provided, the
        prompt instructs the model to preserve scenario intent and address only
        the listed weaknesses (anti-drift measure).

    Returns
    -------
    str
        The complete prompt string ready to send to the LLM.
    """
    template = _load_template()

    # Format list fields as human-readable comma-separated strings, or
    # "none" / "none specified" if empty — avoids confusing "[]" in the prompt.
    desired_indicators_str = (
        ", ".join(spec.desired_indicators)
        if spec.desired_indicators
        else "none specified"
    )
    prohibited_elements_str = (
        ", ".join(spec.prohibited_elements)
        if spec.prohibited_elements
        else "none"
    )
    simulation_constraints_str = (
        json.dumps(spec.simulation_constraints, ensure_ascii=False)
        if spec.simulation_constraints
        else "none"
    )

    # Build the optional revision block.
    if revision_instructions and revision_instructions.strip():
        revision_block = Template(_REVISION_BLOCK_TEMPLATE).safe_substitute(
            revision_instructions=revision_instructions.strip()
        )
    else:
        revision_block = ""

    prompt = Template(template).safe_substitute(
        organization_context=spec.organization_context,
        target_role=spec.target_role,
        scenario_type=spec.scenario_type,
        difficulty=spec.difficulty,
        language=spec.language,
        desired_indicators=desired_indicators_str,
        prohibited_elements=prohibited_elements_str,
        simulation_constraints=simulation_constraints_str,
        revision_block=revision_block,
    )

    return prompt
