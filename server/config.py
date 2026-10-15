"""
server/config.py

Server-only settings. Deliberately separate from the pipeline's own
config/__init__.py (which is never modified) -- this module only adds
things the console needs: paths, CORS origin, and the Live/Demo mode flag.
"""

from __future__ import annotations

import os
from pathlib import Path

import server  # noqa: F401  (ensures REPO_ROOT is on sys.path)

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = REPO_ROOT / "runs"
COMPARE_GROUPS_FILE = RUNS_DIR / "_compare_groups.json"
BENCHMARK_DIR = REPO_ROOT / "scenarios" / "benchmark"
EVAL_RESULTS_DIR = REPO_ROOT / "evaluation" / "results"

RUNS_DIR.mkdir(parents=True, exist_ok=True)

# Vite dev server origin only -- single local user, no auth, per the task's scope.
DEV_CORS_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

HOST = "127.0.0.1"
PORT = int(os.environ.get("PHISHFORGE_SERVER_PORT", "8000"))


_current_mode: str | None = None  # "live" | "demo", lazily initialized from demo_mode_default()


def get_mode() -> str:
    global _current_mode
    if _current_mode is None:
        _current_mode = "demo" if demo_mode_default() else "live"
    return _current_mode


def set_mode(mode: str) -> None:
    global _current_mode
    if mode not in ("live", "demo"):
        raise ValueError(f"Invalid mode: {mode!r}")
    _current_mode = mode


def demo_mode_default() -> bool:
    """
    Whether the server should default to Demo (mock provider) mode.

    PHISHFORGE_DEMO=1 forces demo mode regardless of key presence (useful for
    CI / automated verification, which must never call the live API). If
    unset, default to demo mode unless a real key is configured, so the app
    is usable out of the box without a key.
    """
    env_val = os.environ.get("PHISHFORGE_DEMO")
    if env_val is not None:
        return env_val not in ("0", "false", "False", "")
    import config as core_config  # local import: core_config loads .env at import time

    return not bool(core_config.GEMINI_API_KEY)
