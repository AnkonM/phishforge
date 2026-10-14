"""
server/stats.py

Aggregate computation for GET /api/stats, over whatever RunRecords are
currently stored under runs/ (live + imported). All descriptive only -- no
statistical inference, consistent with the paper's own stance on its small
N. See docs/DESIGN.md / Dashboard page for how these are presented.
"""

from __future__ import annotations

from typing import Any

import config as core_config
from models.schemas.run import RunRecord

DIMENSIONS = ["realism_score", "relevance_score", "indicator_score", "difficulty_score", "language_score"]


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 1) if values else 0.0


def _final_iteration(record: RunRecord) -> dict[str, Any] | None:
    return record.iterations[-1] if record.iterations else None


def compute_stats(records: list[RunRecord]) -> dict[str, Any]:
    total_runs = len(records)
    scores: list[float] = []
    iteration_counts: list[int] = []
    pass_count = 0
    rejected_unsafe_count = 0

    terminal_state_distribution: dict[str, dict[str, int]] = {}
    quality_by_condition: dict[str, dict[str, list[float]]] = {}
    safety_leakage: dict[str, dict[str, int]] = {}
    by_role: dict[str, dict[str, list[Any]]] = {}
    by_difficulty: dict[str, dict[str, list[Any]]] = {}

    for r in records:
        iteration_counts.append(len(r.iterations))
        terminal_state_distribution.setdefault(r.condition, {})
        terminal_state_distribution[r.condition][r.terminal_state] = (
            terminal_state_distribution[r.condition].get(r.terminal_state, 0) + 1
        )
        if r.terminal_state == "PASS":
            pass_count += 1
        if r.terminal_state == "REJECTED_UNSAFE":
            rejected_unsafe_count += 1

        last = _final_iteration(r)
        role_key = r.scenario.target_role
        diff_key = str(r.scenario.difficulty)
        by_role.setdefault(role_key, {"scores": [], "pass": 0, "total": 0})
        by_difficulty.setdefault(diff_key, {"scores": [], "pass": 0, "total": 0})
        by_role[role_key]["total"] += 1
        by_difficulty[diff_key]["total"] += 1
        if r.terminal_state == "PASS":
            by_role[role_key]["pass"] += 1
            by_difficulty[diff_key]["pass"] += 1

        if last is None:
            continue

        ver = last.get("verification")
        score = last.get("score")
        safety_res = last.get("safety_result")

        if score is not None:
            scores.append(score)
            by_role[role_key]["scores"].append(score)
            by_difficulty[diff_key]["scores"].append(score)

        if ver:
            quality_by_condition.setdefault(r.condition, {d: [] for d in DIMENSIONS})
            for d in DIMENSIONS:
                val = ver.get(d)
                if val is not None:
                    quality_by_condition[r.condition][d].append(val)

        safety_leakage.setdefault(r.condition, {"leaked": 0, "total": 0})
        if safety_res is not None and score is not None:
            safety_leakage[r.condition]["total"] += 1
            if not safety_res.get("passed", True) and score >= core_config.PASS_THRESHOLD:
                safety_leakage[r.condition]["leaked"] += 1

    quality_means = {
        cond: {d: _mean(vals) for d, vals in dims.items()} for cond, dims in quality_by_condition.items()
    }

    safety_leakage_out = {
        cond: {
            "leaked": v["leaked"],
            "total": v["total"],
            "rate_pct": round(v["leaked"] / v["total"] * 100, 1) if v["total"] else 0.0,
        }
        for cond, v in safety_leakage.items()
    }

    def _bucket_scores(vals: list[float], width: float = 10.0) -> list[dict[str, Any]]:
        buckets: dict[int, int] = {}
        for v in vals:
            b = int(v // width)
            buckets[b] = buckets.get(b, 0) + 1
        return [
            {"bucket": f"{int(b * width)}-{int(b * width + width - 1)}", "count": c}
            for b, c in sorted(buckets.items())
        ]

    def _bucket_iterations(vals: list[int]) -> list[dict[str, Any]]:
        buckets: dict[int, int] = {}
        for v in vals:
            buckets[v] = buckets.get(v, 0) + 1
        return [{"iterations": k, "count": c} for k, c in sorted(buckets.items())]

    by_role_out = {
        k: {
            "mean_score": _mean(v["scores"]),
            "pass_rate_pct": round(v["pass"] / v["total"] * 100, 1) if v["total"] else 0.0,
            "total": v["total"],
        }
        for k, v in by_role.items()
    }
    by_difficulty_out = {
        k: {
            "mean_score": _mean(v["scores"]),
            "pass_rate_pct": round(v["pass"] / v["total"] * 100, 1) if v["total"] else 0.0,
            "total": v["total"],
        }
        for k, v in by_difficulty.items()
    }

    return {
        "total_runs": total_runs,
        "pass_rate_pct": round(pass_count / total_runs * 100, 1) if total_runs else 0.0,
        "rejected_unsafe_rate_pct": round(rejected_unsafe_count / total_runs * 100, 1) if total_runs else 0.0,
        "mean_iterations": _mean([float(i) for i in iteration_counts]),
        "mean_final_score": _mean(scores),
        "terminal_state_distribution": terminal_state_distribution,
        "safety_leakage": safety_leakage_out,
        "quality_by_condition": quality_means,
        "score_histogram": _bucket_scores(scores),
        "iterations_histogram": _bucket_iterations(iteration_counts),
        "by_role": by_role_out,
        "by_difficulty": by_difficulty_out,
        "n_note": "Descriptive statistics only over the runs stored locally; not the paper's benchmark figures.",
    }
