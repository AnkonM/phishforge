"""
evaluation/human_eval/analyze_human_eval.py

Statistical analysis script for PhishForge human evaluation.
Parses ratings from `rating_packet.md`, joins with `answer_key.json`,
and computes:
  1. Human-vs-Automated alignment (Pearson r & Spearman rho correlations)
  2. Per-condition human rating comparisons (verifier_guided vs baseline_direct)
  3. Analysis of safety-rejected sample perceptions
  4. Exports persistent JSON/CSV reports and markdown analysis summary.
"""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HUMAN_EVAL_DIR = REPO_ROOT / "evaluation" / "human_eval"
PACKET_PATH = HUMAN_EVAL_DIR / "rating_packet.md"
ANSWER_KEY_PATH = HUMAN_EVAL_DIR / "answer_key.json"


def parse_ratings_from_packet(packet_path: Path) -> dict[str, dict[str, Any]]:
    """Extract human ratings from rating_packet.md for each sample_XX ID."""
    content = packet_path.read_text(encoding="utf-8")
    ratings: dict[str, dict[str, Any]] = {}

    pattern = re.compile(r"##\s+Item\s+\d+\s+[—\-–]\s+ID:\s*`?(sample_\d+)`?", re.IGNORECASE)
    splits = pattern.split(content)

    for i in range(1, len(splits), 2):
        sample_id = splits[i]
        block = splits[i + 1]

        r_match = re.search(r"Realism.*?\[(\d+)\]", block)
        rel_match = re.search(r"Role Relevance.*?\[(\d+)\]", block)
        diff_match = re.search(r"Perceived Difficulty.*?\[(\d+)\]", block)
        q_match = re.search(r"Overall Quality.*?\[(\d+)\]", block)
        notes_match = re.search(r"Notes / Observations.*?:([^\n\r]*?)(?:\n\s*---|\Z)", block)

        if r_match and rel_match and diff_match and q_match:
            ratings[sample_id] = {
                "realism": int(r_match.group(1)),
                "relevance": int(rel_match.group(1)),
                "perceived_difficulty": int(diff_match.group(1)),
                "overall_quality": int(q_match.group(1)),
                "notes": notes_match.group(1).strip() if notes_match else "",
            }

    return ratings


def pearson_r(x: list[float], y: list[float]) -> float:
    """Calculate Pearson correlation coefficient r."""
    n = len(x)
    if n < 2:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)
    denom = math.sqrt(var_x * var_y)
    return round(cov / denom, 3) if denom > 0 else 0.0


def spearman_rho(x: list[float], y: list[float]) -> float:
    """Calculate Spearman rank correlation coefficient rho."""
    def _rank(vals: list[float]) -> list[float]:
        sorted_indices = sorted(range(len(vals)), key=lambda k: vals[k])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(vals):
            j = i
            while j < len(vals) - 1 and vals[sorted_indices[j]] == vals[sorted_indices[j + 1]]:
                j += 1
            rank = 1.0 + (i + j) / 2.0
            for k in range(i, j + 1):
                ranks[sorted_indices[k]] = rank
            i = j + 1
        return ranks

    rank_x = _rank(x)
    rank_y = _rank(y)
    return pearson_r(rank_x, rank_y)


def analyze() -> dict[str, Any]:
    """Execute complete human evaluation analysis."""
    ratings = parse_ratings_from_packet(PACKET_PATH)
    with open(ANSWER_KEY_PATH, "r", encoding="utf-8") as f:
        answer_key = json.load(f)

    if len(ratings) != 12:
        raise ValueError(f"Expected 12 parsed ratings, found {len(ratings)}")

    # Combine data rows
    combined_rows: list[dict[str, Any]] = []
    for s_id, r_vals in ratings.items():
        meta = answer_key.get(s_id, {})
        combined_rows.append({
            "sample_id": s_id,
            "condition": meta.get("condition"),
            "terminal_state": meta.get("terminal_state"),
            "target_role": meta.get("target_role"),
            "scenario_type": meta.get("scenario_type"),
            "target_difficulty": meta.get("target_difficulty"),
            "human_realism": r_vals["realism"],
            "human_relevance": r_vals["relevance"],
            "human_difficulty": r_vals["perceived_difficulty"],
            "human_overall": r_vals["overall_quality"],
            "human_notes": r_vals["notes"],
            "auto_overall": meta.get("automated_scores", {}).get("overall_score") if meta.get("automated_scores") else None,
            "auto_realism": meta.get("automated_scores", {}).get("realism_score") if meta.get("automated_scores") else None,
            "auto_relevance": meta.get("automated_scores", {}).get("relevance_score") if meta.get("automated_scores") else None,
            "auto_difficulty": meta.get("automated_scores", {}).get("difficulty_score") if meta.get("automated_scores") else None,
        })

    # Correlation subsets (excluding unscored REJECTED_UNSAFE runs for overall score comparison)
    scored_rows = [r for r in combined_rows if r["auto_overall"] is not None]

    h_overall = [r["human_overall"] for r in scored_rows]
    a_overall = [r["auto_overall"] for r in scored_rows]

    h_realism = [r["human_realism"] for r in scored_rows]
    a_realism = [r["auto_realism"] for r in scored_rows]

    h_relevance = [r["human_relevance"] for r in scored_rows]
    a_relevance = [r["auto_relevance"] for r in scored_rows]

    h_diff = [r["human_difficulty"] for r in combined_rows]
    target_diff = [r["target_difficulty"] for r in combined_rows]

    correlations = {
        "overall_quality_r": pearson_r(h_overall, a_overall),
        "overall_quality_rho": spearman_rho(h_overall, a_overall),
        "realism_r": pearson_r(h_realism, a_realism),
        "realism_rho": spearman_rho(h_realism, a_realism),
        "relevance_r": pearson_r(h_relevance, a_relevance),
        "relevance_rho": spearman_rho(h_relevance, a_relevance),
        "difficulty_level_tracking_r": pearson_r(h_diff, target_diff),
        "difficulty_level_tracking_rho": spearman_rho(h_diff, target_diff),
    }

    # Per-condition averages
    by_condition: dict[str, Any] = {}
    for cond in ["verifier_guided", "baseline_direct"]:
        rows = [r for r in combined_rows if r["condition"] == cond and r["terminal_state"] != "REJECTED_UNSAFE"]
        def _mean(v: list[float]) -> float:
            return round(sum(v) / len(v), 2) if v else 0.0

        by_condition[cond] = {
            "count": len(rows),
            "mean_human_overall": _mean([r["human_overall"] for r in rows]),
            "mean_human_realism": _mean([r["human_realism"] for r in rows]),
            "mean_human_relevance": _mean([r["human_relevance"] for r in rows]),
            "mean_human_difficulty": _mean([r["human_difficulty"] for r in rows]),
        }

    # Safety rejected item inspection
    unsafe_items = [r for r in combined_rows if r["terminal_state"] == "REJECTED_UNSAFE"]

    report_data = {
        "total_rated": len(combined_rows),
        "scored_items_analyzed": len(scored_rows),
        "correlations": correlations,
        "human_means_by_condition": by_condition,
        "safety_rejected_item": unsafe_items[0] if unsafe_items else None,
        "sample_item_breakdown": combined_rows,
    }

    # Save JSON
    out_json = HUMAN_EVAL_DIR / "human_eval_analysis.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Save CSV
    out_csv = HUMAN_EVAL_DIR / "human_eval_analysis.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sample_id", "condition", "terminal_state", "target_role", "scenario_type",
            "target_difficulty", "human_realism", "human_relevance", "human_difficulty",
            "human_overall", "auto_overall", "auto_realism", "auto_relevance", "auto_difficulty", "human_notes"
        ])
        writer.writeheader()
        writer.writerows(combined_rows)

    return report_data


if __name__ == "__main__":
    res = analyze()
    print("Human Evaluation Analysis Completed Successfully!")
    print(json.dumps(res["correlations"], indent=2))
    print("\nMeans by Condition:")
    print(json.dumps(res["human_means_by_condition"], indent=2))
