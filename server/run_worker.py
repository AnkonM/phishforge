"""
server/run_worker.py

Runs the synchronous core pipeline (run_scenario, or the direct+post-hoc
sequence for baseline_direct) in a background thread per request, bridging
its instrumented events to an asyncio-friendly buffer that the SSE endpoint
reads from. See server/pipeline_bridge.py for the instrumentation and
server/mock_provider.py for the Demo-mode scripted LLM.
"""

from __future__ import annotations

import asyncio
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from core.orchestration.run import run_scenario
from models.schemas.run import RunRecord
from models.schemas.scenario import ScenarioSpecification

from server import config as server_config
from server import run_store
from server.mock_provider import build_script, make_clients_for_script, pick_default_script
from server.pipeline_bridge import RunCancelled, make_instrumented_fns, make_on_iteration


class RunHandle:
    def __init__(self, run_id: str, loop: asyncio.AbstractEventLoop) -> None:
        self.run_id = run_id
        self.loop = loop
        self.events: list[dict[str, Any]] = []
        self.new_event = asyncio.Event()
        self.done = False
        self.cancel_event = threading.Event()
        self.cancelled_requested = False
        self.result: RunRecord | None = None
        self.lock = threading.Lock()

    def emit(self, payload: dict[str, Any]) -> None:
        with self.lock:
            self.events.append(payload)

        def _wake() -> None:
            self.new_event.set()

        self.loop.call_soon_threadsafe(_wake)

    def finish(self) -> None:
        with self.lock:
            self.done = True
        self.loop.call_soon_threadsafe(self.new_event.set)


_registry: dict[str, RunHandle] = {}
_registry_lock = threading.Lock()


def get_handle(run_id: str) -> RunHandle | None:
    with _registry_lock:
        return _registry.get(run_id)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_clients(
    spec: ScenarioSpecification, demo_script: str | None, provider_mode: str
) -> tuple[Any, Any, str | None]:
    """Returns (gen_client, judge_client, script_name_used). Both clients are
    None in Live mode (generate()/verify() then build a real genai.Client
    themselves from GEMINI_API_KEY, exactly as the CLI does)."""
    if provider_mode != "demo":
        return None, None, None
    script_name = demo_script or pick_default_script(spec)
    script = build_script(spec, script_name)
    gen_client, judge_client = make_clients_for_script(script)
    return gen_client, judge_client, script_name


def _run_guided(
    handle: RunHandle, spec: ScenarioSpecification, demo_script: str | None, provider_mode: str
) -> RunRecord | None:
    gen_client, judge_client, script_name = _build_clients(spec, demo_script, provider_mode)
    handle.emit({
        "event": "run_started", "run_id": handle.run_id, "ts": _now(),
        "condition": "verifier_guided", "demo_script": script_name,
    })
    gen_fn, safety_fn, verifier_fn, scoring_fn, _ = make_instrumented_fns(
        handle.run_id, handle.emit, handle.cancel_event, gen_client, judge_client,
    )
    on_iteration = make_on_iteration(handle.run_id, handle.emit, handle.cancel_event)
    try:
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
    except RunCancelled:
        return None
    return record


def _run_direct(
    handle: RunHandle, spec: ScenarioSpecification, demo_script: str | None, provider_mode: str
) -> RunRecord | None:
    """Mirrors evaluation/run_benchmark.py's baseline_direct + post-hoc
    evaluation pattern: single-shot generation, then the same safety gate
    and verifier applied after the fact so the UI's "baseline (post-hoc
    checked)" label is literally true."""
    gen_client, judge_client, script_name = _build_clients(spec, demo_script, provider_mode)
    handle.emit({
        "event": "run_started", "run_id": handle.run_id, "ts": _now(),
        "condition": "baseline_direct", "demo_script": script_name,
    })
    gen_fn, safety_fn, verifier_fn, scoring_fn, _ = make_instrumented_fns(
        handle.run_id, handle.emit, handle.cancel_event, gen_client, judge_client,
    )
    try:
        record = run_scenario(spec, condition="baseline_direct", direct_only=True, _generator_fn=gen_fn)
    except RunCancelled:
        return None

    sim_dict = record.iterations[0].get("simulation") if record.iterations else None
    if sim_dict:
        from models.schemas.simulation import GeneratedSimulation

        sim_obj = GeneratedSimulation(**sim_dict)
        if handle.cancel_event.is_set():
            return None
        try:
            # Always run safety + verifier + scoring post-hoc, regardless of
            # the safety outcome -- matching evaluation/run_benchmark.py's
            # baseline_direct pattern exactly. This is deliberate: the
            # Dashboard's safety-leakage metric needs to know the quality
            # score baseline output *would have* received even when it also
            # violates the gate, to show "would have been approved without
            # the gate" (terminal_state stays the pipeline's own
            # GENERATED_UNVERIFIED / GENERATION_FAILURE -- never invented).
            safety_res = safety_fn(sim_obj)
            ver_res = verifier_fn(spec, sim_obj)
            ver_res = ver_res.model_copy(
                update={"safety_status": safety_res.status, "safety_findings": safety_res.findings}
            )
            scored_ver = scoring_fn(ver_res)
            record.iterations[0]["safety_result"] = safety_res.model_dump(mode="json")
            record.iterations[0]["verification"] = scored_ver.model_dump(mode="json")
            record.iterations[0]["score"] = scored_ver.overall_score
        except RunCancelled:
            return None
    return record


def _execute(
    handle: RunHandle, spec: ScenarioSpecification, run_mode: str, demo_script: str | None, provider_mode: str
) -> None:
    try:
        if run_mode == "guided":
            record = _run_guided(handle, spec, demo_script, provider_mode)
        else:
            record = _run_direct(handle, spec, demo_script, provider_mode)

        if record is None:
            handle.emit({
                "event": "run_finished", "run_id": handle.run_id, "ts": _now(),
                "terminal_state": "CANCELLED", "cancelled": True,
            })
            handle.result = None
        else:
            # run_scenario() mints its own internal run_id, independent of
            # the id this worker already generated and handed to the client
            # (for the SSE URL and CreateRunResponse) -- reconcile them here
            # so the persisted file, the SSE run_id, and the API-visible id
            # are always the same value. RunRecord.run_id has no invariant
            # tying it to run_scenario()'s internals; overriding it on the
            # already-returned object is purely a server-side bookkeeping
            # fix, not a change to core behavior.
            record = record.model_copy(update={"run_id": handle.run_id})
            run_store.save(record)
            handle.result = record
            handle.emit({
                "event": "run_finished", "run_id": handle.run_id, "ts": _now(),
                "terminal_state": record.terminal_state,
                "cancelled": handle.cancel_event.is_set(),
                "record": record.model_dump(mode="json"),
            })
    except Exception as exc:  # noqa: BLE001 -- surface any unexpected failure to the client
        handle.emit({
            "event": "error", "run_id": handle.run_id, "ts": _now(),
            "stage": "run", "message": str(exc),
        })
        handle.emit({
            "event": "run_finished", "run_id": handle.run_id, "ts": _now(),
            "terminal_state": "ERROR", "cancelled": False,
        })
    finally:
        handle.finish()


def start_run(
    loop: asyncio.AbstractEventLoop, spec: ScenarioSpecification, run_mode: str, demo_script: str | None = None
) -> str:
    """run_mode: 'guided' | 'direct'. `loop` must be the running event loop,
    captured by the (async) caller -- this is called from a sync endpoint
    function that FastAPI may run in a worker thread, where
    asyncio.get_running_loop() would fail. Provider mode (live/demo) is read
    from the current global Settings toggle at call time."""
    run_id = str(uuid.uuid4())
    handle = RunHandle(run_id, loop)
    provider_mode = server_config.get_mode()
    with _registry_lock:
        _registry[run_id] = handle
    thread = threading.Thread(
        target=_execute, args=(handle, spec, run_mode, demo_script, provider_mode), daemon=True
    )
    thread.start()
    return run_id


def start_compare(
    loop: asyncio.AbstractEventLoop, spec: ScenarioSpecification, demo_script: str | None = None
) -> tuple[str, list[str]]:
    guided_id = start_run(loop, spec, "guided", demo_script)
    direct_id = start_run(loop, spec, "direct", demo_script)
    group_id = str(uuid.uuid4())
    run_store.set_compare_group(group_id, [guided_id, direct_id])
    return group_id, [guided_id, direct_id]


def request_cancel(run_id: str) -> bool:
    handle = get_handle(run_id)
    if handle is None or handle.done:
        return False
    handle.cancelled_requested = True
    handle.cancel_event.set()
    return True
