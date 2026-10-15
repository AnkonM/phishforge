from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from server import benchmark_runner, run_worker
from server import config as server_config
from server.app import create_app

# Background worker threads call `loop.call_soon_threadsafe(...)` on the
# event loop that was running when the request that spawned them was
# handled. Starlette's SYNC TestClient tears its event loop down after each
# call (it opens a fresh anyio portal per call), so a worker thread's
# callback arrives after the loop is already closed -- it silently fails to
# deliver, and the SSE endpoint's `await handle.new_event.wait()` then hangs
# forever waiting for a wakeup that can never come. A real uvicorn process
# has exactly one persistent loop for the app's whole lifetime, so this is a
# TestClient-only artifact, not a production bug -- confirmed by the manual
# curl smoke test against a real running server (see docs/DECISIONS.md). The
# fix here is to use httpx.AsyncClient directly inside async test functions,
# which keeps one event loop alive across every await in the test (matching
# the real server), instead of starlette.testclient.TestClient.


@pytest.fixture(autouse=True)
def isolated_runs_dir(tmp_path, monkeypatch):
    """Every test gets its own empty runs/ directory and demo mode, so tests
    never depend on or pollute the real runs/ folder, and never call the
    live API."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    monkeypatch.setattr(server_config, "RUNS_DIR", runs_dir)
    monkeypatch.setattr(server_config, "_current_mode", "demo")
    run_worker._registry.clear()
    benchmark_runner._registry.clear()
    yield


@pytest_asyncio.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture
def sample_spec() -> dict:
    return {
        "organization_context": "Test Corp, a 50-person software company.",
        "target_role": "it",
        "scenario_type": "password_alert",
        "difficulty": 1,
        "language": "en",
        "desired_indicators": ["urgency", "suspicious_link", "generic_greeting"],
    }
