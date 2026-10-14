from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from models.schemas.run import RunRecord
from server import run_store, run_worker
from server.models import CreateRunRequest, CreateRunResponse, RunDetailResponse, RunSummary
from server.sse import format_sse

router = APIRouter(tags=["runs"])


def _summary(record: RunRecord) -> RunSummary:
    last = record.iterations[-1] if record.iterations else None
    return RunSummary(
        run_id=record.run_id,
        created_at=record.created_at,
        target_role=record.scenario.target_role,
        scenario_type=record.scenario.scenario_type,
        difficulty=record.scenario.difficulty,
        condition=record.condition,
        terminal_state=record.terminal_state,
        final_score=last.get("score") if last else None,
        iteration_count=len(record.iterations),
        compare_group_id=run_store.compare_group_for(record.run_id),
        imported=run_store.is_imported(record.run_id),
    )


@router.post("/runs", response_model=CreateRunResponse, status_code=202)
async def create_run(body: CreateRunRequest) -> CreateRunResponse:
    loop = asyncio.get_running_loop()
    if body.mode == "compare":
        group_id, run_ids = run_worker.start_compare(loop, body.spec, body.demo_script)
        return CreateRunResponse(compare_group_id=group_id, run_ids=run_ids)
    run_id = run_worker.start_run(loop, body.spec, body.mode, body.demo_script)
    return CreateRunResponse(run_id=run_id)


@router.get("/runs/{run_id}/events")
async def run_events(run_id: str):
    handle = run_worker.get_handle(run_id)
    if handle is None:
        raise HTTPException(404, "Unknown run_id (not an active or recent run).")

    async def generator():
        last_sent = 0
        try:
            while True:
                while last_sent < len(handle.events):
                    yield format_sse(handle.events[last_sent])
                    last_sent += 1
                if handle.done and last_sent >= len(handle.events):
                    break
                handle.new_event.clear()
                try:
                    await asyncio.wait_for(handle.new_event.wait(), timeout=30)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            # Client disconnected -- nothing else to clean up, the worker
            # thread owns its own lifecycle independent of any listener.
            raise

    return StreamingResponse(generator(), media_type="text/event-stream")


@router.get("/runs", response_model=list[RunSummary])
def list_runs(
    state: str | None = Query(default=None),
    role: str | None = Query(default=None),
    difficulty: int | None = Query(default=None),
    mode: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> list[RunSummary]:
    records = run_store.list_all()
    out = []
    for r in records:
        if state and r.terminal_state != state:
            continue
        if role and r.scenario.target_role != role:
            continue
        if difficulty and r.scenario.difficulty != difficulty:
            continue
        if mode and r.condition != mode:
            continue
        if q:
            haystack = " ".join(
                [r.scenario.organization_context, r.scenario.scenario_type, r.run_id, r.scenario.target_role]
            ).lower()
            if q.lower() not in haystack:
                continue
        out.append(_summary(r))
    out.sort(key=lambda s: s.created_at, reverse=True)
    return out


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str) -> RunDetailResponse:
    record = run_store.get(run_id)
    if record is None:
        raise HTTPException(404, "Run not found.")
    return RunDetailResponse(
        record=record,
        compare_group_id=run_store.compare_group_for(run_id),
        imported=run_store.is_imported(run_id),
    )


@router.delete("/runs/{run_id}", status_code=204)
def delete_run(run_id: str) -> None:
    if not run_store.delete(run_id):
        raise HTTPException(404, "Run not found.")


@router.post("/runs/{run_id}/cancel")
def cancel_run(run_id: str) -> dict[str, bool]:
    ok = run_worker.request_cancel(run_id)
    return {"cancelled": ok}
