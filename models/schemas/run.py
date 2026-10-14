"""
RunRecord schema.

The top-level record for a complete PhishForge run, covering all iterations.
This is exactly what gets serialised to the --out JSON file via run_writer.py.

Source of truth: authoritative field definitions (v2 correction, 2026-08-27).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from models.schemas.scenario import ScenarioSpecification


# Terminal states a run can end in (FR6 in Document A v2 §13).
TerminalState = Literal[
    "PASS",
    "FAILED_TO_CONVERGE",
    "REJECTED_UNSAFE",
    "GENERATION_FAILURE",
    "GENERATED_UNVERIFIED",
]

# Experimental condition — only "verifier_guided" is reachable in the current
# CLI-only build. "baseline_static" and "baseline_direct" are Future Scope
# (Document A v2 §16 / Document C v2 Future Phase A). The field is included
# now so RunRecord's shape doesn't need to change when baselines are added.
# The CLI sets this to "verifier_guided" always (or "baseline_direct" for
# --direct-only runs, since that flag skips safety/verify/refine).
Condition = Literal[
    "baseline_static",
    "baseline_direct",
    "verifier_guided",
]


class RunRecord(BaseModel):
    """
    Complete record of a PhishForge run — all iterations, all scores,
    and the terminal outcome.

    Serialised to JSON by core/storage/run_writer.py.
    Each element of `iterations` is a dict with keys:
      simulation, safety_result, verification, score, refinement
    (populated by core/orchestration/run.py).
    """

    # ------------------------------------------------------------------
    # Run identity
    # ------------------------------------------------------------------

    run_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID uniquely identifying this run.",
    )

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    scenario: ScenarioSpecification = Field(
        ...,
        description="The scenario specification that was run.",
    )

    # ------------------------------------------------------------------
    # Experimental condition
    # ------------------------------------------------------------------

    condition: Condition = Field(
        ...,
        description=(
            "Which pipeline condition was run. "
            "Use 'verifier_guided' for the full pipeline; "
            "'baseline_direct' for --direct-only runs."
        ),
    )

    # ------------------------------------------------------------------
    # Iteration history
    # ------------------------------------------------------------------

    iterations: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Ordered list of per-iteration dicts. "
            "Each dict contains: simulation, safety_result, verification, "
            "score, refinement — all serialised to dict by the orchestration layer."
        ),
    )

    # ------------------------------------------------------------------
    # Terminal outcome
    # ------------------------------------------------------------------

    terminal_state: TerminalState = Field(
        ...,
        description="How the run ended (FR6).",
    )

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the run started.",
    )
