"""
evaluation/aggregate_metrics.py

Metric aggregation and statistical comparison engine for PhishForge benchmarks.
Loads all RunRecord artifacts from `evaluation/results/` and computes comprehensive
per-condition performance tables across quality dimensions, pass rates, safety rates,
iteration counts, and terminal outcome distributions.

Outputs both formatted console tables and persistent CSV/JSON summary artifacts.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import config
from core.storage.run_writer import load_run
from models.schemas.run import RunRecord


def aggregate_metrics(
    results_dir: str | Path = REPO_ROOT / "evaluation" / "results",
) -> dict[str, Any]:
    """Aggregate benchmark results across verifier_guided and baseline_direct conditions."""
    results_dir = Path(results_dir)
    record_files = list(results_dir.glob("*.json"))

    # Exclude summary files
    record_files = [f for f in record_files if not f.name.startswith("summary_metrics")]

    if not record_files:
        print(f"No RunRecord JSON files found in {results_dir}")
        return {}

    records: list[RunRecord] = []
    for rf in record_files:
        try:
            records.append(load_run(rf))
        except Exception as e:
            print(f"Warning: Failed to load {rf.name}: {e}", file=sys.stderr)

    conditions = ["verifier_guided", "baseline_direct"]
    metrics_by_condition: dict[str, dict[str, Any]] = {}

    for cond in conditions:
        cond_records = [r for r in records if r.condition == cond]
        count = len(cond_records)

        scores: list[float] = []
        realism_scores: list[float] = []
        relevance_scores: list[float] = []
        indicator_scores: list[float] = []
        difficulty_scores: list[float] = []
        language_scores: list[float] = []

        pass_count = 0
        safety_pass_count = 0
        iterations_list: list[int] = []
        terminal_states: dict[str, int] = {}

        for r in cond_records:
            # Track terminal states
            terminal_states[r.terminal_state] = terminal_states.get(r.terminal_state, 0) + 1
            iterations_list.append(len(r.iterations))

            # Inspect final iteration
            if r.iterations:
                last_iter = r.iterations[-1]
                
                # Safety evaluation
                safety_res = last_iter.get("safety_result")
                if safety_res and safety_res.get("passed") is True:
                    safety_pass_count += 1
                elif cond == "baseline_direct" and r.terminal_state == "GENERATED_UNVERIFIED" and not safety_res:
                    # If direct_only had no post-hoc, count as unverified
                    pass

                # Quality evaluation
                ver = last_iter.get("verification")
                if ver and ver.get("overall_score") is not None:
                    q = ver["overall_score"]
                    scores.append(q)
                    if q >= config.PASS_THRESHOLD:
                        pass_count += 1
                    
                    realism_scores.append(ver.get("realism_score", 0.0))
                    relevance_scores.append(ver.get("relevance_score", 0.0))
                    indicator_scores.append(ver.get("indicator_score", 0.0))
                    difficulty_scores.append(ver.get("difficulty_score", 0.0))
                    language_scores.append(ver.get("language_score", 0.0))

        def _mean(vals: list[float]) -> float:
            return round(sum(vals) / len(vals), 1) if vals else 0.0

        metrics_by_condition[cond] = {
            "total_runs": count,
            "mean_overall_score": _mean(scores),
            "pass_rate_pct": round((pass_count / count * 100), 1) if count else 0.0,
            "safety_pass_rate_pct": round((safety_pass_count / count * 100), 1) if count else 0.0,
            "mean_realism": _mean(realism_scores),
            "mean_role_relevance": _mean(relevance_scores),
            "mean_indicator_coverage": _mean(indicator_scores),
            "mean_difficulty_match": _mean(difficulty_scores),
            "mean_language_quality": _mean(language_scores),
            "mean_iterations": _mean([float(i) for i in iterations_list]),
            "terminal_state_distribution": terminal_states,
        }

    # Print comparative ASCII table
    print("\n" + "=" * 80)
    print("                PHISHFORGE BENCHMARK COMPARATIVE METRICS")
    print("=" * 80)
    print(f"{'Metric':<35} | {'verifier_guided':<18} | {'baseline_direct':<18}")
    print("-" * 80)
    
    vg = metrics_by_condition.get("verifier_guided", {})
    bd = metrics_by_condition.get("baseline_direct", {})

    rows = [
        ("Total Scenarios Evaluated", vg.get("total_runs", 0), bd.get("total_runs", 0)),
        ("Mean Overall Quality Score (Q)", f"{vg.get('mean_overall_score', 0.0)} / 100", f"{bd.get('mean_overall_score', 0.0)} / 100"),
        ("Pass Rate (Q >= 80.0)", f"{vg.get('pass_rate_pct', 0.0)}%", f"{bd.get('pass_rate_pct', 0.0)}%"),
        ("Safety Gate Pass Rate", f"{vg.get('safety_pass_rate_pct', 0.0)}%", f"{bd.get('safety_pass_rate_pct', 0.0)}%"),
        ("Mean Realism Score", vg.get("mean_realism", 0.0), bd.get("mean_realism", 0.0)),
        ("Mean Role Relevance Score", vg.get("mean_role_relevance", 0.0), bd.get("mean_role_relevance", 0.0)),
        ("Mean Indicator Coverage", vg.get("mean_indicator_coverage", 0.0), bd.get("mean_indicator_coverage", 0.0)),
        ("Mean Difficulty Match", vg.get("mean_difficulty_match", 0.0), bd.get("mean_difficulty_match", 0.0)),
        ("Mean Language Quality", vg.get("mean_language_quality", 0.0), bd.get("mean_language_quality", 0.0)),
        ("Mean Iterations to Terminate", vg.get("mean_iterations", 0.0), bd.get("mean_iterations", 0.0)),
    ]

    for label, v_val, b_val in rows:
        print(f"{label:<35} | {str(v_val):<18} | {str(b_val):<18}")
    
    print("-" * 80)
    print(f"Terminal States (verifier_guided) : {vg.get('terminal_state_distribution', {})}")
    print(f"Terminal States (baseline_direct) : {bd.get('terminal_state_distribution', {})}")
    print("=" * 80 + "\n")

    # Export to JSON
    json_path = results_dir / "summary_metrics.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics_by_condition, f, indent=2)
    print(f"Saved JSON metrics to: {json_path}")

    # Export to CSV
    csv_path = results_dir / "summary_metrics.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "verifier_guided", "baseline_direct"])
        for label, v_val, b_val in rows:
            writer.writerow([label, v_val, b_val])
    print(f"Saved CSV metrics to: {csv_path}\n")

    return metrics_by_condition


if __name__ == "__main__":
    aggregate_metrics()
