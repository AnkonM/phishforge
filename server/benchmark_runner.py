"""
server/benchmark_runner.py

Runs the 12 benchmark presets under both conditions (verifier_guided +
baseline_direct = 24 pipeline runs) sequentially in a background thread,
emitting progress events. Each sub-run reuses run_worker's own
_run_guided/_run_direct + RunHandle machinery and is persisted exactly like
any run created from Studio, so results feed the Dashboard identically.
"""

from __future__ import annotations

import asyncio
import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from models.schemas.scenario import ScenarioSpecification

from server import run_store
from server.config import BENCHMARK_DIR
from server.mock_provider import pick_default_script
from server.run_worker import RunHandle, _run_direct, _run_guided


class BenchmarkHandle:
    def __init__(self, benchmark_id: str, loop: asyncio.AbstractEventLoop) -> None:
        self.benchmark_id = benchmark_id
        self.loop = loop
        self.events: list[dict[str, Any]] = []
        self.new_event = asyncio.Event()
        self.done = False
        self.lock = threading.Lock()

    def emit(self, payload: dict[str, Any]) -> None:
        with self.lock:
            self.events.append(payload)
        self.loop.call_soon_threadsafe(self.new_event.set)

    def finish(self) -> None:
        with self.lock:
            self.done = True
        self.loop.call_soon_threadsafe(self.new_event.set)


_registry: dict[str, BenchmarkHandle] = {}
_lock = threading.Lock()


def get_handle(benchmark_id: str) -> BenchmarkHandle | None:
    with _lock:
        return _registry.get(benchmark_id)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_presets() -> list[ScenarioSpecification]:
    specs = []
    for path in sorted(BENCHMARK_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        specs.append(ScenarioSpecification(**data))
    return specs


def _execute(handle: BenchmarkHandle, provider_mode: str) -> None:
    try:
        specs = load_presets()
        total = len(specs) * 2
        handle.emit({
            "event": "benchmark_started", "benchmark_id": handle.benchmark_id, "ts": _now(),
            "total": total, "mode": provider_mode,
        })
        idx = 0
        for spec in specs:
            for run_mode, condition_label in (("guided", "verifier_guided"), ("direct", "baseline_direct")):
                idx += 1
                handle.emit({
                    "event": "scenario_started", "benchmark_id": handle.benchmark_id, "ts": _now(),
                    "index": idx, "total": total, "scenario_id": spec.scenario_id, "condition": condition_label,
                })
                run_id = str(uuid.uuid4())
                sub_handle = RunHandle(run_id, handle.loop)
                demo_script = pick_default_script(spec) if provider_mode == "demo" else None
                try:
                    if run_mode == "guided":
                        record = _run_guided(sub_handle, spec, demo_script, provider_mode)
                    else:
                        record = _run_direct(sub_handle, spec, demo_script, provider_mode)
                except Exception as exc:  # noqa: BLE001
                    handle.emit({
                        "event": "scenario_error", "benchmark_id": handle.benchmark_id, "ts": _now(),
                        "index": idx, "scenario_id": spec.scenario_id, "condition": condition_label,
                        "message": str(exc),
                    })
                    continue

                if record is None:
                    handle.emit({
                        "event": "scenario_error", "benchmark_id": handle.benchmark_id, "ts": _now(),
                        "index": idx, "scenario_id": spec.scenario_id, "condition": condition_label,
                        "message": "cancelled",
                    })
                    continue

                # reconcile run_scenario()'s own internal run_id with the id
                # this benchmark run already minted -- see run_worker._execute
                # for why this reconciliation is needed and why it's safe.
                record = record.model_copy(update={"run_id": run_id})
                run_store.save(record)
                final_score = record.iterations[-1].get("score") if record.iterations else None
                handle.emit({
                    "event": "scenario_finished", "benchmark_id": handle.benchmark_id, "ts": _now(),
                    "index": idx, "total": total, "scenario_id": spec.scenario_id, "condition": condition_label,
                    "run_id": run_id, "terminal_state": record.terminal_state, "score": final_score,
                })
        handle.emit({"event": "benchmark_finished", "benchmark_id": handle.benchmark_id, "ts": _now()})
    except Exception as exc:  # noqa: BLE001
        handle.emit({"event": "error", "benchmark_id": handle.benchmark_id, "ts": _now(), "message": str(exc)})
    finally:
        handle.finish()


def start_benchmark(loop: asyncio.AbstractEventLoop, provider_mode: str) -> str:
    benchmark_id = str(uuid.uuid4())
    handle = BenchmarkHandle(benchmark_id, loop)
    with _lock:
        _registry[benchmark_id] = handle
    thread = threading.Thread(target=_execute, args=(handle, provider_mode), daemon=True)
    thread.start()
    return benchmark_id
