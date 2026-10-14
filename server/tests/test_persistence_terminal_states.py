"""
Confirms a RunRecord is persisted under runs/ for every terminal state the
pipeline can reach, including the two failure states (REJECTED_UNSAFE,
GENERATION_FAILURE) that are easy to forget to persist.
"""

from __future__ import annotations

import threading

import pytest

from server import run_store
from server.pipeline_bridge import make_instrumented_fns, make_on_iteration
from server.tests.test_runs_lifecycle import _drain_sse


async def _run_and_get_terminal_state(client, spec, demo_script):
    resp = await client.post("/api/runs", json={"spec": spec, "mode": "guided", "demo_script": demo_script})
    run_id = resp.json()["run_id"]
    events = await _drain_sse(client, f"/api/runs/{run_id}/events")
    return run_id, events[-1]["terminal_state"]


@pytest.mark.asyncio
async def test_pass_is_persisted(client, sample_spec):
    run_id, state = await _run_and_get_terminal_state(client, sample_spec, "first_pass")
    assert state == "PASS"
    assert run_store.get(run_id) is not None
    assert run_store.get(run_id).terminal_state == "PASS"


@pytest.mark.asyncio
async def test_rejected_unsafe_is_persisted(client, sample_spec):
    run_id, state = await _run_and_get_terminal_state(client, sample_spec, "safety_reject")
    assert state == "REJECTED_UNSAFE"
    record = run_store.get(run_id)
    assert record is not None
    assert record.terminal_state == "REJECTED_UNSAFE"
    assert record.iterations[0]["safety_result"]["passed"] is False


@pytest.mark.asyncio
async def test_failed_to_converge_is_persisted(client, sample_spec):
    run_id, state = await _run_and_get_terminal_state(client, sample_spec, "plateau")
    assert state == "FAILED_TO_CONVERGE"
    record = run_store.get(run_id)
    assert record is not None
    assert record.terminal_state == "FAILED_TO_CONVERGE"
    assert len(record.iterations) == 3


def test_generation_failure_terminal_state_and_events(sample_spec):
    """Unit-level (sync, no HTTP/event-loop involved): a generator that
    always raises GenerationFailure must propagate to
    terminal_state=GENERATION_FAILURE, and the instrumented gen_fn wrapper
    must emit an "error" event before run_scenario's own except clause
    swallows the exception."""
    from core.generation.generator import GenerationFailure
    from core.orchestration.run import run_scenario
    from models.schemas.scenario import ScenarioSpecification

    spec = ScenarioSpecification(**sample_spec)
    events: list[dict] = []
    cancel_event = threading.Event()

    gen_fn, safety_fn, verifier_fn, scoring_fn, _ = make_instrumented_fns(
        "test-run", events.append, cancel_event,
    )

    import server.pipeline_bridge as pb

    original = pb.generate
    pb.generate = lambda *a, **k: (_ for _ in ()).throw(GenerationFailure("scripted test failure"))
    try:
        on_iteration = make_on_iteration("test-run", events.append, cancel_event)
        record = run_scenario(
            spec,
            condition="verifier_guided",
            on_iteration=on_iteration,
            direct_only=False,
            _generator_fn=gen_fn,
            _safety_gate_fn=safety_fn,
            _verifier_fn=verifier_fn,
            _scoring_fn=scoring_fn,
        )
    finally:
        pb.generate = original

    assert record.terminal_state == "GENERATION_FAILURE"
    assert any(e["event"] == "error" and e.get("stage") == "generation" for e in events)
