"""
core/verification/verifier.py

Hybrid Verifier entry point. Merges Layer A (deterministic rule checks)
and Layer B (LLM-based semantic judge) into a single VerificationResult.

Source of truth: Document B v2 §12.

Architecture rules (Document B v2 §7):
  - No print() statements.
  - No CLI-specific logic.
  - Returns a schema-valid VerificationResult.
"""

from __future__ import annotations

import uuid
from typing import Any

from core.verification.llm_judge import run_llm_judge
from core.verification.rule_checks import run_rule_checks
from models.schemas.scenario import ScenarioSpecification
from models.schemas.simulation import GeneratedSimulation
from models.schemas.verification import VerificationResult

VERIFIER_VERSION = "rules-v1+llm-v1"


def verify(
    spec: ScenarioSpecification,
    simulation: GeneratedSimulation,
    *,
    _client: Any = None,
) -> VerificationResult:
    """
    Execute hybrid verification on a generated simulation artifact.

    Parameters
    ----------
    spec:
        The target scenario specification.
    simulation:
        The generated simulation under evaluation.
    _client:
        Optional injected Gemini client or mock for Layer B.

    Returns
    -------
    VerificationResult
        Complete multi-dimensional evaluation result.
        Note: overall_score and pass_fail are initialized to baseline placeholders
        (0.0 / 'FAIL') to be computed and classified by the Phase 5 Scoring Engine.
        safety_status and safety_findings are initialized to 'PASS'/[] placeholders
        to be reconciled by the Phase 6 Orchestration pipeline.
    """
    # 1. Run Layer A deterministic rule checks
    layer_a = run_rule_checks(spec, simulation)

    # 2. Run Layer B LLM semantic judge
    layer_b = run_llm_judge(spec, simulation, _client=_client)

    # 3. Merge semantic findings
    combined_findings = layer_b.semantic_findings + layer_a.rule_findings

    # 4. Construct unified VerificationResult
    return VerificationResult(
        verification_id=str(uuid.uuid4()),
        generation_id=simulation.generation_id,
        realism_score=layer_b.realism_score,
        relevance_score=layer_b.relevance_score,
        difficulty_score=layer_b.difficulty_score,
        indicator_score=layer_a.indicator_score,
        language_score=layer_a.language_score,
        safety_status="PASS",
        safety_findings=[],
        semantic_findings=combined_findings,
        overall_score=0.0,
        pass_fail="FAIL",
        verifier_version=VERIFIER_VERSION,
    )
