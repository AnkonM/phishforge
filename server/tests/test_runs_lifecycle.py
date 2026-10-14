from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.asyncio


async def _drain_sse(client, url: str) -> list[dict]:
    events = []
    async with client.stream("GET", url) as resp:
        assert resp.status_code == 200
        buf = ""
        async for chunk in resp.aiter_text():
            buf += chunk
            while "\n\n" in buf:
                frame, buf = buf.split("\n\n", 1)
                if frame.startswith("data: "):
                    events.append(json.loads(frame[len("data: "):]))
    return events


async def test_create_guided_run_reaches_terminal_state(client, sample_spec):
    resp = await client.post("/api/runs", json={"spec": sample_spec, "mode": "guided"})
    assert resp.status_code == 202
    run_id = resp.json()["run_id"]
    events = await _drain_sse(client, f"/api/runs/{run_id}/events")
    names = [e["event"] for e in events]
    assert names[0] == "run_started"
    assert names[-1] == "run_finished"
    assert events[-1]["terminal_state"] in {"PASS", "REJECTED_UNSAFE", "FAILED_TO_CONVERGE", "GENERATION_FAILURE"}

    detail = await client.get(f"/api/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["record"]["run_id"] == run_id


async def test_create_direct_run_is_post_hoc_checked(client, sample_spec):
    resp = await client.post("/api/runs", json={"spec": sample_spec, "mode": "direct"})
    run_id = resp.json()["run_id"]
    events = await _drain_sse(client, f"/api/runs/{run_id}/events")
    assert any(e["event"] == "verification_result" for e in events)
    assert any(e["event"] == "safety_result" for e in events)
    final = events[-1]
    assert final["terminal_state"] == "GENERATED_UNVERIFIED"

    detail = (await client.get(f"/api/runs/{run_id}")).json()
    assert detail["record"]["iterations"][0]["verification"] is not None


async def test_create_compare_run_links_two_records(client, sample_spec):
    resp = await client.post("/api/runs", json={"spec": sample_spec, "mode": "compare"})
    assert resp.status_code == 202
    body = resp.json()
    assert body["compare_group_id"]
    assert len(body["run_ids"]) == 2

    for run_id in body["run_ids"]:
        await _drain_sse(client, f"/api/runs/{run_id}/events")

    conditions = set()
    for run_id in body["run_ids"]:
        detail = (await client.get(f"/api/runs/{run_id}")).json()
        assert detail["compare_group_id"] == body["compare_group_id"]
        conditions.add(detail["record"]["condition"])
    assert conditions == {"verifier_guided", "baseline_direct"}


async def test_demo_script_explicit_selection(client, sample_spec):
    for script, expected_state in [
        ("first_pass", "PASS"),
        ("safety_reject", "REJECTED_UNSAFE"),
        ("plateau", "FAILED_TO_CONVERGE"),
    ]:
        resp = await client.post(
            "/api/runs", json={"spec": sample_spec, "mode": "guided", "demo_script": script}
        )
        run_id = resp.json()["run_id"]
        events = await _drain_sse(client, f"/api/runs/{run_id}/events")
        assert events[-1]["terminal_state"] == expected_state, f"script={script}"


async def test_revise_pass_bench01_replay_scores(client):
    spec = {
        "scenario_id": "bench-01-it-pwd-d1",
        "organization_context": "Global tech consulting firm, 1200 employees. IT department uses Okta for SSO.",
        "target_role": "it",
        "scenario_type": "password_alert",
        "difficulty": 1,
        "desired_indicators": ["urgency", "suspicious_link", "generic_greeting"],
    }
    resp = await client.post("/api/runs", json={"spec": spec, "mode": "guided"})
    run_id = resp.json()["run_id"]
    events = await _drain_sse(client, f"/api/runs/{run_id}/events")
    scores = [e["overall_score"] for e in events if e["event"] == "score_result"]
    assert scores == [72.8, 92.8]
    assert events[-1]["terminal_state"] == "PASS"


async def test_list_filter_search_delete(client, sample_spec):
    resp = await client.post(
        "/api/runs", json={"spec": sample_spec, "mode": "guided", "demo_script": "first_pass"}
    )
    run_id = resp.json()["run_id"]
    await _drain_sse(client, f"/api/runs/{run_id}/events")

    all_runs = (await client.get("/api/runs")).json()
    assert any(r["run_id"] == run_id for r in all_runs)

    by_state = (await client.get("/api/runs", params={"state": "PASS"})).json()
    assert any(r["run_id"] == run_id for r in by_state)

    by_role = (await client.get("/api/runs", params={"role": "it"})).json()
    assert any(r["run_id"] == run_id for r in by_role)

    by_bad_role = (await client.get("/api/runs", params={"role": "finance"})).json()
    assert not any(r["run_id"] == run_id for r in by_bad_role)

    by_search = (await client.get("/api/runs", params={"q": "Test Corp"})).json()
    assert any(r["run_id"] == run_id for r in by_search)

    del_resp = await client.delete(f"/api/runs/{run_id}")
    assert del_resp.status_code == 204
    assert (await client.get(f"/api/runs/{run_id}")).status_code == 404
    assert (await client.delete(f"/api/runs/{run_id}")).status_code == 404


async def test_cancel_unknown_run_returns_false(client):
    resp = await client.post("/api/runs/does-not-exist/cancel")
    assert resp.json() == {"cancelled": False}
