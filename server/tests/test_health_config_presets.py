from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_health_demo_mode(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "demo"
    assert "key_configured" in data


async def test_health_mode_toggle(client):
    resp = await client.put("/api/health/mode", json={"mode": "live"})
    assert resp.status_code == 200
    assert resp.json()["mode"] == "live"
    resp = await client.put("/api/health/mode", json={"mode": "demo"})
    assert resp.json()["mode"] == "demo"


async def test_config_shape(client):
    resp = await client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pass_threshold"] == 80
    assert data["revise_threshold"] == 60
    assert data["max_iterations"] == 3
    assert abs(sum(data["scoring_weights"].values()) - 1.0) < 1e-6
    assert len(data["safety_rules"]) == 5
    assert len(data["difficulty_rubric"]) == 4
    assert set(data["supported_roles"]) == {"finance", "hr", "it", "sales", "operations", "executive"}


async def test_presets_count_and_shape(client):
    resp = await client.get("/api/presets")
    assert resp.status_code == 200
    presets = resp.json()
    assert len(presets) == 12
    ids = {p["scenario_id"] for p in presets}
    assert "bench-01-it-pwd-d1" in ids
    for p in presets:
        assert p["target_role"] in {"finance", "hr", "it", "sales", "operations", "executive"}
        assert 1 <= p["difficulty"] <= 4
