from __future__ import annotations

from fastapi import APIRouter

import config as core_config
from server import config as server_config
from server.models import HealthResponse, ReachabilityResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(
        mode=server_config.get_mode(),
        key_configured=bool(core_config.GEMINI_API_KEY),
    )


@router.put("/health/mode", response_model=HealthResponse)
def put_mode(body: dict) -> HealthResponse:
    mode = body.get("mode")
    server_config.set_mode(mode)
    return HealthResponse(mode=server_config.get_mode(), key_configured=bool(core_config.GEMINI_API_KEY))


@router.post("/health/reachability", response_model=ReachabilityResponse)
def reachability_test() -> ReachabilityResponse:
    """A lightweight reachability probe for the configured Gemini key -- does
    NOT run the pipeline or spend generation tokens, just confirms the API
    is reachable and the key is accepted by listing available models."""
    if not core_config.GEMINI_API_KEY:
        return ReachabilityResponse(reachable=False, detail="No GEMINI_API_KEY configured.")
    try:
        import google.genai as genai

        client = genai.Client(api_key=core_config.GEMINI_API_KEY)
        next(iter(client.models.list()), None)
        return ReachabilityResponse(reachable=True, detail="Gemini API reachable.")
    except Exception as exc:  # noqa: BLE001
        return ReachabilityResponse(reachable=False, detail=f"Unreachable: {exc}")
