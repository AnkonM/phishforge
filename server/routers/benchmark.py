from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from server import benchmark_runner
from server.models import BenchmarkCreateResponse, BenchmarkRequest
from server.sse import format_sse

router = APIRouter(tags=["benchmark"])


@router.post("/benchmark", response_model=BenchmarkCreateResponse, status_code=202)
async def create_benchmark(body: BenchmarkRequest) -> BenchmarkCreateResponse:
    loop = asyncio.get_running_loop()
    benchmark_id = benchmark_runner.start_benchmark(loop, body.mode)
    return BenchmarkCreateResponse(benchmark_id=benchmark_id)


@router.get("/benchmark/{benchmark_id}/events")
async def benchmark_events(benchmark_id: str):
    handle = benchmark_runner.get_handle(benchmark_id)
    if handle is None:
        raise HTTPException(404, "Unknown benchmark_id.")

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
            raise

    return StreamingResponse(generator(), media_type="text/event-stream")
