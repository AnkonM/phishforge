"""
server/pipeline_bridge.py

Bridges the synchronous core pipeline to a stream of fine-grained SSE
events, without modifying any core file. Two techniques, both purely
additive:

1. The four stage-function injection points `run_scenario()` already
   exposes for testing (_generator_fn, _safety_gate_fn, _verifier_fn,
   _scoring_fn) are given instrumented wrappers that call the REAL stage
   function and emit a progress event before/after. This is how the UI
   gets Generator/Safety Gate/Verifier/Scoring-level granularity even
   though the real `on_iteration` callback only reports once per iteration.

2. Best-effort cancellation: raising a RunCancelled from inside
   safety_fn/verifier_fn/scoring_fn/on_iteration propagates straight out of
   run_scenario (none of those call sites catch exceptions). Raising it
   from gen_fn gets swallowed into a GENERATION_FAILURE terminal state by
   run.py's own `except (GenerationFailure, Exception)` -- so the worker
   also re-checks the cancel flag after run_scenario returns to relabel
   that case. See docs/DECISIONS.md.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Callable

from core.generation.generator import GenerationFailure, generate
from core.refinement.refinement_controller import build_instructions
from core.safety.safety_gate import check as check_safety
from core.scoring.scoring_engine import compute as compute_score
from core.verification.verifier import verify as verify_simulation
from models.schemas.scenario import ScenarioSpecification

Emit = Callable[[dict[str, Any]], None]


class RunCancelled(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_instrumented_fns(
    run_id: str,
    emit: Emit,
    cancel_event: threading.Event,
    gen_client: Any = None,
    judge_client: Any = None,
):
    """Returns (gen_fn, safety_fn, verifier_fn, scoring_fn, get_iteration) for
    injection into run_scenario(). `get_iteration()` returns the iteration
    number most recently started (gen_fn is called exactly once per
    iteration attempt in both direct and loop modes)."""

    iteration_counter = {"n": 0}

    def get_iteration() -> int:
        return iteration_counter["n"]

    def gen_fn(spec: ScenarioSpecification, revision_instructions: str | None = None):
        iteration_counter["n"] += 1
        n = iteration_counter["n"]
        emit({"event": "iteration_started", "run_id": run_id, "iteration": n, "ts": _now()})
        if cancel_event.is_set():
            raise RunCancelled()
        emit({"event": "generation_started", "run_id": run_id, "iteration": n, "ts": _now()})
        try:
            sim = generate(spec, revision_instructions=revision_instructions, _client=gen_client)
        except GenerationFailure as exc:
            emit({
                "event": "error", "run_id": run_id, "iteration": n, "ts": _now(),
                "stage": "generation", "message": str(exc),
            })
            raise
        emit({
            "event": "generation_complete", "run_id": run_id, "iteration": n, "ts": _now(),
            "simulation": sim.model_dump(mode="json"),
        })
        return sim

    def safety_fn(sim):
        if cancel_event.is_set():
            raise RunCancelled()
        n = iteration_counter["n"]
        res = check_safety(sim)
        emit({
            "event": "safety_result", "run_id": run_id, "iteration": n, "ts": _now(),
            "result": res.model_dump(mode="json"),
        })
        return res

    def verifier_fn(spec, sim):
        if cancel_event.is_set():
            raise RunCancelled()
        n = iteration_counter["n"]
        res = verify_simulation(spec, sim, _client=judge_client)
        emit({
            "event": "verification_result", "run_id": run_id, "iteration": n, "ts": _now(),
            "result": res.model_dump(mode="json"),
        })
        return res

    def scoring_fn(ver_res):
        if cancel_event.is_set():
            raise RunCancelled()
        n = iteration_counter["n"]
        scored = compute_score(ver_res)
        emit({
            "event": "score_result", "run_id": run_id, "iteration": n, "ts": _now(),
            "overall_score": scored.overall_score, "pass_fail": scored.pass_fail,
            "result": scored.model_dump(mode="json"),
        })
        # build_instructions is a pure, zero-LLM function -- this is exactly
        # what core.refinement.refinement_controller.create_refinement_result
        # computes internally for this same VerificationResult regardless of
        # whether the run continues or terminates here, so it is safe and
        # accurate to compute (not invent) eagerly for the live stream.
        emit({
            "event": "refinement_instruction", "run_id": run_id, "iteration": n, "ts": _now(),
            "instructions": build_instructions(scored),
            "weaknesses": scored.semantic_findings,
        })
        return scored

    return gen_fn, safety_fn, verifier_fn, scoring_fn, get_iteration


def make_on_iteration(run_id: str, emit: Emit, cancel_event: threading.Event):
    def on_iteration(iteration_number, sim, ver, safety, status):
        if cancel_event.is_set():
            raise RunCancelled()
        payload: dict[str, Any] = {
            "event": "iteration_status", "run_id": run_id, "iteration": iteration_number,
            "ts": _now(), "status": status,
        }
        emit(payload)
        # refinement_instruction itself is emitted from scoring_fn (see above) --
        # it's computed there via the same pure build_instructions() call run.py
        # uses internally, before run.py even decides whether to terminate or continue.

    return on_iteration
