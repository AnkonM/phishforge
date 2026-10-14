from __future__ import annotations

import asyncio

import pytest

from server.tests.test_runs_lifecycle import _drain_sse

pytestmark = pytest.mark.asyncio


async def test_two_concurrent_runs_do_not_cross_contaminate(client, sample_spec):
    spec_a = {**sample_spec, "target_role": "it"}
    spec_b = {**sample_spec, "target_role": "finance"}

    resp_a, resp_b = await asyncio.gather(
        client.post("/api/runs", json={"spec": spec_a, "mode": "guided", "demo_script": "first_pass"}),
        client.post("/api/runs", json={"spec": spec_b, "mode": "guided", "demo_script": "plateau"}),
    )
    run_id_a = resp_a.json()["run_id"]
    run_id_b = resp_b.json()["run_id"]
    assert run_id_a != run_id_b

    events_a, events_b = await asyncio.gather(
        _drain_sse(client, f"/api/runs/{run_id_a}/events"),
        _drain_sse(client, f"/api/runs/{run_id_b}/events"),
    )

    for e in events_a:
        assert e["run_id"] == run_id_a
    for e in events_b:
        assert e["run_id"] == run_id_b

    assert events_a[-1]["terminal_state"] == "PASS"
    assert events_b[-1]["terminal_state"] == "FAILED_TO_CONVERGE"

    detail_a, detail_b = await asyncio.gather(
        client.get(f"/api/runs/{run_id_a}"), client.get(f"/api/runs/{run_id_b}")
    )
    assert detail_a.status_code == 200
    assert detail_b.status_code == 200
