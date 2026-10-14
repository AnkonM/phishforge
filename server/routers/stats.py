from __future__ import annotations

from fastapi import APIRouter

from server import run_store
from server.models import StatsResponse
from server.stats import compute_stats

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats() -> StatsResponse:
    records = run_store.list_all()
    return StatsResponse(**compute_stats(records))
