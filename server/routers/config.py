"""
server/routers/config.py

GET /api/config -- read-only pipeline configuration. Every value is derived
directly from the real source (config/__init__.py constants, the safety
gate's own function docstrings, the verifier prompt template's rubric text)
rather than retyped by hand, so it can never silently drift from what the
pipeline actually does.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

from fastapi import APIRouter

import config as core_config
from core.safety import safety_gate
from server.models import ConfigResponse, DifficultyLevelInfo, SafetyRuleInfo

router = APIRouter(tags=["config"])

_VERIFIER_PROMPT = (
    Path(__file__).resolve().parent.parent.parent / "prompts" / "verifier" / "v1_verifier.txt"
)

_RUBRIC_LINE = re.compile(r"Level (\d) — (\w+): (.+)")

_SAFETY_RULE_FNS = [
    safety_gate.check_no_real_domains,
    safety_gate.check_no_credential_harvesting,
    safety_gate.check_no_attachment_payloads,
    safety_gate.check_no_real_brand_impersonation,
    safety_gate.check_no_real_pii,
]


def _difficulty_rubric() -> list[DifficultyLevelInfo]:
    text = _VERIFIER_PROMPT.read_text(encoding="utf-8")
    levels = []
    for match in _RUBRIC_LINE.finditer(text):
        levels.append(
            DifficultyLevelInfo(level=int(match.group(1)), label=match.group(2), description=match.group(3).strip())
        )
    return levels


def _safety_rules() -> list[SafetyRuleInfo]:
    rules = []
    for fn in _SAFETY_RULE_FNS:
        doc = inspect.getdoc(fn) or ""
        first_para = doc.split("\n\n")[0].strip().replace("\n", " ")
        rules.append(SafetyRuleInfo(name=fn.__name__, description=first_para))
    return rules


@router.get("/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    return ConfigResponse(
        scoring_weights=core_config.SCORING_WEIGHTS,
        pass_threshold=core_config.PASS_THRESHOLD,
        revise_threshold=core_config.REVISE_THRESHOLD,
        max_iterations=core_config.MAX_ITERATIONS,
        improvement_epsilon=core_config.IMPROVEMENT_EPSILON,
        improvement_patience=core_config.IMPROVEMENT_PATIENCE,
        supported_roles=core_config.SUPPORTED_ROLES,
        supported_scenario_types=core_config.SUPPORTED_SCENARIO_TYPES,
        safety_rules=_safety_rules(),
        difficulty_rubric=_difficulty_rubric(),
        model_name=core_config.MODEL_NAME,
    )
