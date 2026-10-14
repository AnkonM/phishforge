"""
evaluation/human_eval/select_sample.py

Deterministic sample selector for human evaluation round.
Draws a balanced 12-item sample from `evaluation/results/`:
  - 5 verifier_guided (PASS)
  - 1 verifier_guided (REJECTED_UNSAFE sanity check)
  - 6 baseline_direct

Strips all condition labels, score metadata, run IDs, and verifier critique findings.
Generates:
  1. `evaluation/human_eval/rating_packet.md` (blind questionnaire for the human rater)
  2. `evaluation/human_eval/answer_key.json` (secret lookup table for post-evaluation analysis)
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = REPO_ROOT / "evaluation" / "results"
HUMAN_EVAL_DIR = REPO_ROOT / "evaluation" / "human_eval"


def generate_human_eval_packet(seed: int = 42) -> None:
    """Select 12 benchmark runs and compile anonymized rating packet + secret answer key."""
    HUMAN_EVAL_DIR.mkdir(parents=True, exist_ok=True)

    vg_files = sorted(RESULTS_DIR.glob("verifier_guided_*.json"))
    bd_files = sorted(RESULTS_DIR.glob("baseline_direct_*.json"))

    if not vg_files or not bd_files:
        raise FileNotFoundError(f"RunRecord artifacts not found in {RESULTS_DIR}")

    vg_pass: list[dict[str, Any]] = []
    vg_unsafe: list[dict[str, Any]] = []
    bd_records: list[dict[str, Any]] = []

    for f in vg_files:
        with open(f, "r", encoding="utf-8") as jf:
            data = json.load(jf)
            if data.get("terminal_state") == "PASS":
                vg_pass.append(data)
            elif data.get("terminal_state") == "REJECTED_UNSAFE":
                vg_unsafe.append(data)

    for f in bd_files:
        with open(f, "r", encoding="utf-8") as jf:
            bd_records.append(json.load(jf))

    rng = random.Random(seed)

    # Sample selections: 5 PASS, 1 UNSAFE, 6 BASELINE
    selected_vg_pass = rng.sample(vg_pass, 5)
    selected_vg_unsafe = rng.sample(vg_unsafe, 1)
    selected_bd = rng.sample(bd_records, 6)

    combined_sample = selected_vg_pass + selected_vg_unsafe + selected_bd
    rng.shuffle(combined_sample)

    answer_key: dict[str, Any] = {}
    packet_sections: list[str] = [
        "# PhishForge Human Evaluation: Blind Rating Packet\n",
        "Please rate the following 12 simulations independently based on the scenario context provided. "
        "Refer to [`rubric_reference.md`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/rubric_reference.md) "
        "and [`instructions.md`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/instructions.md) for rating criteria.\n",
        "---\n",
    ]

    for idx, item in enumerate(combined_sample, 1):
        sample_id = f"sample_{idx:02d}"
        scenario = item["scenario"]
        last_iter = item["iterations"][-1]
        sim = last_iter.get("simulation") or {}
        ver = last_iter.get("verification") or {}

        # 1. Record in secret answer key
        answer_key[sample_id] = {
            "condition": item["condition"],
            "run_id": item["run_id"],
            "scenario_id": scenario["scenario_id"],
            "target_role": scenario["target_role"],
            "scenario_type": scenario["scenario_type"],
            "target_difficulty": scenario["difficulty"],
            "terminal_state": item["terminal_state"],
            "automated_scores": {
                "overall_score": ver.get("overall_score"),
                "realism_score": ver.get("realism_score"),
                "relevance_score": ver.get("relevance_score"),
                "difficulty_score": ver.get("difficulty_score"),
                "indicator_score": ver.get("indicator_score"),
                "language_score": ver.get("language_score"),
            } if ver else None,
        }

        # 2. Format anonymized rating packet item (NO scores, NO condition, NO findings)
        sec = [
            f"## Item {idx} — ID: `{sample_id}`\n",
            "### Scenario Target Context",
            f"- **Target Role**: `{scenario.get('target_role', 'N/A')}`",
            f"- **Scenario Type**: `{scenario.get('scenario_type', 'N/A')}`",
            f"- **Target Difficulty**: Level {scenario.get('difficulty', 'N/A')} (Scale 1–4)",
            f"- **Organization Context**: {scenario.get('organization_context', 'N/A')}\n",
            "### Training Simulation Content",
            f"**Subject**: {sim.get('subject', 'N/A')}\n",
            f"**Sender**: {sim.get('sender', 'N/A')}\n",
            "**Body**:",
            "```text",
            sim.get("body", "N/A"),
            "```\n",
            "### Your Evaluation Ratings",
            "- **Realism (1–5)**: [ ]",
            "- **Role Relevance (1–5)**: [ ]",
            "- **Perceived Difficulty (1–4)**: [ ]",
            "- **Overall Quality (1–5)**: [ ]",
            "- **Notes / Observations (optional)**: ",
            "\n---\n",
        ]
        packet_sections.append("\n".join(sec))

    # Add quick summary fill table at bottom
    packet_sections.append("## Summary Ratings Table\n")
    packet_sections.append("| Sample ID | Target Role | Target Diff | Realism (1-5) | Relevance (1-5) | Perceived Diff (1-4) | Overall Quality (1-5) |")
    packet_sections.append("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for idx, item in enumerate(combined_sample, 1):
        sample_id = f"sample_{idx:02d}"
        role = item["scenario"].get("target_role", "N/A")
        diff = item["scenario"].get("difficulty", "N/A")
        packet_sections.append(f"| `{sample_id}` | `{role}` | Level {diff} | | | | |")

    # Write files
    packet_file = HUMAN_EVAL_DIR / "rating_packet.md"
    packet_file.write_text("\n".join(packet_sections), encoding="utf-8")

    answer_key_file = HUMAN_EVAL_DIR / "answer_key.json"
    answer_key_file.write_text(json.dumps(answer_key, indent=2), encoding="utf-8")

    print(f"Generated human evaluation rating packet: {packet_file}")
    print(f"Generated secret answer key: {answer_key_file}")


if __name__ == "__main__":
    generate_human_eval_packet()
