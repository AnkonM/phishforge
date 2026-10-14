from __future__ import annotations

import pytest

from server.tests.test_runs_lifecycle import _drain_sse

pytestmark = pytest.mark.asyncio

EXPECTED_PER_ITERATION_ORDER = [
    "iteration_started",
    "generation_started",
    "generation_complete",
    "safety_result",
    "verification_result",
    "score_result",
    "refinement_instruction",
    "iteration_status",
]


async def test_guided_revise_pass_event_schema_and_ordering(client, sample_spec):
    resp = await client.post(
        "/api/runs", json={"spec": sample_spec, "mode": "guided", "demo_script": "revise_pass"}
    )
    run_id = resp.json()["run_id"]
    events = await _drain_sse(client, f"/api/runs/{run_id}/events")

    assert events[0]["event"] == "run_started"
    assert events[-1]["event"] == "run_finished"

    for e in events:
        assert e["run_id"] == run_id
        assert "ts" in e

    iter1 = [e["event"] for e in events if e.get("iteration") == 1]
    iter2 = [e["event"] for e in events if e.get("iteration") == 2]
    assert iter1 == EXPECTED_PER_ITERATION_ORDER
    assert iter2 == EXPECTED_PER_ITERATION_ORDER

    final = events[-1]
    assert final["terminal_state"] == "PASS"
    assert "record" in final


async def test_safety_reject_short_circuits_before_verification(client, sample_spec):
    resp = await client.post(
        "/api/runs", json={"spec": sample_spec, "mode": "guided", "demo_script": "safety_reject"}
    )
    run_id = resp.json()["run_id"]
    events = await _drain_sse(client, f"/api/runs/{run_id}/events")
    names = [e["event"] for e in events]
    assert "safety_result" in names
    assert "verification_result" not in names
    assert "score_result" not in names
    assert events[-1]["terminal_state"] == "REJECTED_UNSAFE"


async def test_error_event_never_leaks_api_key(client, sample_spec, monkeypatch):
    import config as core_config

    # Patch both the cached module constant AND the raw env var -- generate()
    # falls back to os.environ.get("GEMINI_API_KEY") directly, and this test
    # must never risk a real network call if only one were cleared.
    monkeypatch.setattr(core_config, "GEMINI_API_KEY", None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    resp = await client.put("/api/health/mode", json={"mode": "live"})
    assert resp.status_code == 200
    resp = await client.post("/api/runs", json={"spec": sample_spec, "mode": "guided"})
    run_id = resp.json()["run_id"]
    events = await _drain_sse(client, f"/api/runs/{run_id}/events")
    assert events[-1]["terminal_state"] == "GENERATION_FAILURE"
    for e in events:
        assert "GEMINI_API_KEY" not in str(e) or "is not set" in str(e)
    await client.put("/api/health/mode", json={"mode": "demo"})
