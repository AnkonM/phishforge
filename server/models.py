"""
server/models.py

Server-only Pydantic DTOs for the Console API. These are NOT the core
pipeline schemas (models/schemas/*) -- those are imported and reused
directly wherever a request/response needs the real ScenarioSpecification
or RunRecord shape. These DTOs exist only for endpoints that need a shape
the core pipeline has no reason to define (health, config, run summaries,
stats, benchmark progress).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from models.schemas.run import Condition, RunRecord, TerminalState
from models.schemas.scenario import ScenarioSpecification

RunMode = Literal["guided", "direct", "compare"]
ProviderMode = Literal["live", "demo"]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    mode: ProviderMode
    key_configured: bool


class SafetyRuleInfo(BaseModel):
    name: str
    description: str


class DifficultyLevelInfo(BaseModel):
    level: int
    label: str
    description: str


class ConfigResponse(BaseModel):
    scoring_weights: dict[str, float]
    pass_threshold: float
    revise_threshold: float
    max_iterations: int
    improvement_epsilon: float
    improvement_patience: int
    supported_roles: list[str]
    supported_scenario_types: list[str]
    safety_rules: list[SafetyRuleInfo]
    difficulty_rubric: list[DifficultyLevelInfo]
    model_name: str


DemoScriptName = Literal["first_pass", "revise_pass", "safety_reject", "plateau"]


class CreateRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec: ScenarioSpecification
    mode: RunMode = "guided"
    demo_script: DemoScriptName | None = Field(
        default=None,
        description="Demo-mode only: explicitly choose a scripted scenario instead of the auto-picked default.",
    )


class CreateRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str | None = None
    compare_group_id: str | None = None
    run_ids: list[str] | None = None


class RunSummary(BaseModel):
    run_id: str
    created_at: datetime
    target_role: str
    scenario_type: str
    difficulty: int
    condition: Condition
    terminal_state: TerminalState
    final_score: float | None
    iteration_count: int
    compare_group_id: str | None = None
    imported: bool = False


class RunDetailResponse(BaseModel):
    record: RunRecord
    compare_group_id: str | None = None
    imported: bool = False


class ReachabilityResponse(BaseModel):
    reachable: bool
    detail: str


class BenchmarkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: ProviderMode = "demo"


class BenchmarkCreateResponse(BaseModel):
    benchmark_id: str


class StatsResponse(BaseModel):
    total_runs: int
    pass_rate_pct: float
    rejected_unsafe_rate_pct: float
    mean_iterations: float
    mean_final_score: float
    terminal_state_distribution: dict[str, dict[str, int]]  # by mode -> {state: count}
    safety_leakage: dict[str, dict[str, float | int]]  # mode -> {leaked, total, rate_pct}
    quality_by_condition: dict[str, dict[str, float]]  # condition -> {dimension: mean}
    score_histogram: list[dict[str, str | int]]
    iterations_histogram: list[dict[str, int]]
    by_role: dict[str, dict[str, float | int]]
    by_difficulty: dict[str, dict[str, float | int]]
    n_note: str = "Descriptive statistics only over the runs stored locally; not the paper's benchmark figures."


class ErrorResponse(BaseModel):
    detail: str


__all__ = [
    "RunMode",
    "ProviderMode",
    "HealthResponse",
    "SafetyRuleInfo",
    "DifficultyLevelInfo",
    "ConfigResponse",
    "CreateRunRequest",
    "CreateRunResponse",
    "RunSummary",
    "RunDetailResponse",
    "ReachabilityResponse",
    "BenchmarkRequest",
    "BenchmarkCreateResponse",
    "StatsResponse",
    "ErrorResponse",
]
