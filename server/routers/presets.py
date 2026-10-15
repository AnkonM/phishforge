from __future__ import annotations

from fastapi import APIRouter

from models.schemas.scenario import ScenarioSpecification
from server.benchmark_runner import load_presets

router = APIRouter(tags=["presets"])


@router.get("/presets", response_model=list[ScenarioSpecification])
def get_presets() -> list[ScenarioSpecification]:
    return load_presets()
