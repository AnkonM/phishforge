"""
The Gemini API key must never appear in any response body, on any endpoint,
under any mode. This test exercises every documented endpoint and asserts
the raw key string (read directly from .env, not from any server code path)
never shows up.
"""

from __future__ import annotations

import json

import pytest

import config as core_config
from server.tests.test_runs_lifecycle import _drain_sse

pytestmark = pytest.mark.asyncio


async def test_key_never_appears_in_any_response(client, sample_spec):
    key = core_config.GEMINI_API_KEY
    assert key, "Test requires a real-looking key configured in .env to be meaningful."

    bodies = []
    bodies.append((await client.get("/api/health")).text)
    bodies.append((await client.get("/api/config")).text)
    bodies.append((await client.get("/api/presets")).text)
    bodies.append((await client.get("/api/stats")).text)
    bodies.append((await client.get("/api/runs")).text)

    resp = await client.post(
        "/api/runs", json={"spec": sample_spec, "mode": "guided", "demo_script": "revise_pass"}
    )
    run_id = resp.json()["run_id"]
    events = await _drain_sse(client, f"/api/runs/{run_id}/events")
    bodies.append(json.dumps(events))
    bodies.append((await client.get(f"/api/runs/{run_id}")).text)

    for body in bodies:
        assert key not in body
