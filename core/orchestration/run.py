"""
core/orchestration/run.py

Top-level orchestration engine for PhishForge.

Wires together Generator, Safety Gate, Hybrid Verifier, Scoring Engine,
and Refinement Controller into the closed-loop synthesis pipeline.

Source of truth: Document B v2 §4, §6.5, §7, §15.

Precedence of termination policies:
  1. Safety Gate rejection (status == FAIL) -> immediate REJECTED_UNSAFE
  2. Scoring threshold met (pass_fail == PASS) -> PASS
  3. Iteration ceiling reached (iteration >= MAX_ITERATIONS) -> FAILED_TO_CONVERGE (MAX_ITERATIONS)
  4. Non-improving delta plateau (should_stop_early) -> FAILED_TO_CONVERGE (NO_IMPROVEMENT)

Architecture rules (Document B v2 §7):
  - No print() statements in core modules.
  - User presentation is delegated to the optional on_iteration callback.
  - Returns a validated RunRecord.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable

import config
from core.generation.generator import GenerationFailure, generate
from core.refinement.refinement_controller import (
    build_instructions,
    create_refinement_result,
    should_stop_early,
)
from core.safety.safety_gate import SafetyCheckResult, check as check_safety
from core.scoring.scoring_engine import compute as compute_score
from core.verification.verifier import verify as verify_simulation
from models.schemas.run import Condition, RunRecord, TerminalState
from models.schemas.scenario import ScenarioSpecification
from models.schemas.simulation import GeneratedSimulation
from models.schemas.verification import VerificationResult

# Callback type signature: (iteration_number, simulation, verification, safety_result, loop_status)
IterationCallback = Callable[
    [
        int,
        GeneratedSimulation | None,
        VerificationResult | None,
        SafetyCheckResult | None,
        str,
    ],
    None,
]


def run_scenario(
    spec: ScenarioSpecification,
    condition: Condition = "verifier_guided",
    on_iteration: IterationCallback | None = None,
    direct_only: bool = False,
    *,
    _generator_fn: Any = None,
    _safety_gate_fn: Any = None,
    _verifier_fn: Any = None,
    _scoring_fn: Any = None,
) -> RunRecord:
    """
    Execute a full PhishForge synthesis run for a ScenarioSpecification.

    Parameters
    ----------
    spec:
        The target ScenarioSpecification to synthesize.
    condition:
        Experimental condition ('verifier_guided' or 'baseline_direct').
    on_iteration:
        Optional observer callback invoked after each iteration step.
    direct_only:
        If True, executes single-shot generation bypassing safety, verification,
        and refinement (condition='baseline_direct').
    _generator_fn, _safety_gate_fn, _verifier_fn, _scoring_fn:
        Optional function injections for testing and mocking without live API calls.

    Returns
    -------
    RunRecord
        The complete serializable record containing iteration history,
        all artifacts, scores, and the terminal outcome.
    """
    gen_fn = _generator_fn or generate
    safety_fn = _safety_gate_fn or check_safety
    ver_fn = _verifier_fn or verify_simulation
    score_fn = _scoring_fn or compute_score

    run_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    iterations: list[dict[str, Any]] = []

    # -----------------------------------------------------------------------
    # Direct-Only Mode (Baseline Direct Condition)
    # -----------------------------------------------------------------------
    if direct_only:
        try:
            sim = gen_fn(spec)
            terminal_state: TerminalState = "GENERATED_UNVERIFIED"
            iteration_data = {
                "iteration_number": 1,
                "simulation": sim.model_dump(mode="json"),
                "safety_result": None,
                "verification": None,
                "score": None,
                "refinement": None,
            }
            iterations.append(iteration_data)
            if on_iteration:
                on_iteration(1, sim, None, None, "GENERATED_UNVERIFIED")
        except (GenerationFailure, Exception):
            terminal_state = "GENERATION_FAILURE"
            iterations.append({
                "iteration_number": 1,
                "simulation": None,
                "safety_result": None,
                "verification": None,
                "score": None,
                "refinement": None,
            })
            if on_iteration:
                on_iteration(1, None, None, None, "GENERATION_FAILURE")

        return RunRecord(
            run_id=run_id,
            scenario=spec,
            condition="baseline_direct",
            iterations=iterations,
            terminal_state=terminal_state,
            created_at=created_at,
        )

    # -----------------------------------------------------------------------
    # Closed-Loop Verifier-Guided Synthesis Mode
    # -----------------------------------------------------------------------
    max_iterations = config.MAX_ITERATIONS
    score_history: list[float] = []
    revision_instructions: str | None = None

    for iteration_idx in range(1, max_iterations + 1):
        # 1. Generation step
        try:
            sim = gen_fn(spec, revision_instructions=revision_instructions)
        except (GenerationFailure, Exception):
            iterations.append({
                "iteration_number": iteration_idx,
                "simulation": None,
                "safety_result": None,
                "verification": None,
                "score": None,
                "refinement": None,
            })
            if on_iteration:
                on_iteration(iteration_idx, None, None, None, "GENERATION_FAILURE")
            return RunRecord(
                run_id=run_id,
                scenario=spec,
                condition="verifier_guided",
                iterations=iterations,
                terminal_state="GENERATION_FAILURE",
                created_at=created_at,
            )

        # 2. Safety Gate evaluation
        safety_res = safety_fn(sim)
        if not safety_res.passed:
            prior_score = score_history[-1] if score_history else None
            refinement = create_refinement_result(
                iteration_number=iteration_idx,
                verification=None,
                prior_score=prior_score,
                termination_reason="SAFETY_FAIL",
            )
            iterations.append({
                "iteration_number": iteration_idx,
                "simulation": sim.model_dump(mode="json"),
                "safety_result": safety_res.model_dump(mode="json"),
                "verification": None,
                "score": None,
                "refinement": refinement.model_dump(mode="json"),
            })
            if on_iteration:
                on_iteration(iteration_idx, sim, None, safety_res, "REJECTED_UNSAFE")
            return RunRecord(
                run_id=run_id,
                scenario=spec,
                condition="verifier_guided",
                iterations=iterations,
                terminal_state="REJECTED_UNSAFE",
                created_at=created_at,
            )

        # 3. Hybrid Verification & Scoring
        ver_res = ver_fn(spec, sim)
        # Reconcile authoritative Safety Gate findings onto verification result
        ver_res = ver_res.model_copy(
            update={
                "safety_status": safety_res.status,
                "safety_findings": safety_res.findings,
            }
        )
        scored_ver = score_fn(ver_res)

        prior_score = score_history[-1] if score_history else None
        current_score = scored_ver.overall_score
        score_history.append(current_score)

        # 4. Check Termination Policies in Exact Precedence
        # Policy 2: Score meets PASS threshold (>= 80.0)
        if scored_ver.pass_fail == config.BAND_PASS:
            refinement = create_refinement_result(
                iteration_number=iteration_idx,
                verification=scored_ver,
                prior_score=prior_score,
                termination_reason="PASS",
            )
            iterations.append({
                "iteration_number": iteration_idx,
                "simulation": sim.model_dump(mode="json"),
                "safety_result": safety_res.model_dump(mode="json"),
                "verification": scored_ver.model_dump(mode="json"),
                "score": current_score,
                "refinement": refinement.model_dump(mode="json"),
            })
            if on_iteration:
                on_iteration(iteration_idx, sim, scored_ver, safety_res, "PASS")
            return RunRecord(
                run_id=run_id,
                scenario=spec,
                condition="verifier_guided",
                iterations=iterations,
                terminal_state="PASS",
                created_at=created_at,
            )

        # Policy 3: Hard iteration ceiling reached
        if iteration_idx >= max_iterations:
            refinement = create_refinement_result(
                iteration_number=iteration_idx,
                verification=scored_ver,
                prior_score=prior_score,
                termination_reason="MAX_ITERATIONS",
            )
            iterations.append({
                "iteration_number": iteration_idx,
                "simulation": sim.model_dump(mode="json"),
                "safety_result": safety_res.model_dump(mode="json"),
                "verification": scored_ver.model_dump(mode="json"),
                "score": current_score,
                "refinement": refinement.model_dump(mode="json"),
            })
            if on_iteration:
                on_iteration(iteration_idx, sim, scored_ver, safety_res, "FAILED_TO_CONVERGE")
            return RunRecord(
                run_id=run_id,
                scenario=spec,
                condition="verifier_guided",
                iterations=iterations,
                terminal_state="FAILED_TO_CONVERGE",
                created_at=created_at,
            )

        # Policy 4: Stalled improvement (epsilon/patience triggered)
        if should_stop_early(score_history):
            refinement = create_refinement_result(
                iteration_number=iteration_idx,
                verification=scored_ver,
                prior_score=prior_score,
                termination_reason="NO_IMPROVEMENT",
            )
            iterations.append({
                "iteration_number": iteration_idx,
                "simulation": sim.model_dump(mode="json"),
                "safety_result": safety_res.model_dump(mode="json"),
                "verification": scored_ver.model_dump(mode="json"),
                "score": current_score,
                "refinement": refinement.model_dump(mode="json"),
            })
            if on_iteration:
                on_iteration(iteration_idx, sim, scored_ver, safety_res, "FAILED_TO_CONVERGE")
            return RunRecord(
                run_id=run_id,
                scenario=spec,
                condition="verifier_guided",
                iterations=iterations,
                terminal_state="FAILED_TO_CONVERGE",
                created_at=created_at,
            )

        # 5. Continue to Next Iteration (REVISE)
        revision_instructions = build_instructions(scored_ver)
        refinement = create_refinement_result(
            iteration_number=iteration_idx,
            verification=scored_ver,
            prior_score=prior_score,
            termination_reason=None,
        )
        iterations.append({
            "iteration_number": iteration_idx,
            "simulation": sim.model_dump(mode="json"),
            "safety_result": safety_res.model_dump(mode="json"),
            "verification": scored_ver.model_dump(mode="json"),
            "score": current_score,
            "refinement": refinement.model_dump(mode="json"),
        })
        if on_iteration:
            on_iteration(iteration_idx, sim, scored_ver, safety_res, "REVISE")

    # Fallback safety return (structurally unreachable due to loop range return)
    return RunRecord(
        run_id=run_id,
        scenario=spec,
        condition="verifier_guided",
        iterations=iterations,
        terminal_state="FAILED_TO_CONVERGE",
        created_at=created_at,
    )
