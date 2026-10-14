"""
evaluation/run_benchmark.py

Benchmark runner executing the curated benchmark suite (12 scenarios) across
two experimental conditions:
  1. `verifier_guided` (PhishForge closed-loop synthesis: generation -> safety -> verify -> score -> refine)
  2. `baseline_direct` (Single-shot generation without in-loop verification or refinement)

Post-hoc verification and scoring is applied to `baseline_direct` simulations so both
conditions can be directly compared on identical quality and safety dimensions.

Artifacts are persisted as JSON RunRecords under `evaluation/results/`.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import config
from core.orchestration.run import run_scenario
from core.safety.safety_gate import check as check_safety
from core.scoring.scoring_engine import compute as compute_score
from core.storage.run_writer import save_run
from core.verification.verifier import verify as verify_simulation
from models.schemas.run import RunRecord
from models.schemas.scenario import ScenarioSpecification


def run_benchmark(
    benchmark_dir: str | Path = REPO_ROOT / "scenarios" / "benchmark",
    results_dir: str | Path = REPO_ROOT / "evaluation" / "results",
) -> None:
    """Execute all benchmark scenarios under both conditions and save RunRecords."""
    benchmark_dir = Path(benchmark_dir)
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    scenario_files = sorted(benchmark_dir.glob("*.json"))
    total_scenarios = len(scenario_files)

    if total_scenarios == 0:
        print(f"No scenario JSON files found in {benchmark_dir}")
        return

    print("=" * 80)
    print(f"STARTING PHISHFORGE BENCHMARK SUITE ({total_scenarios} Scenarios x 2 Conditions = {total_scenarios * 2} Runs)")
    print(f"Model: {config.MODEL_NAME}")
    print(f"Results Directory: {results_dir}")
    print("=" * 80)

    start_time = time.time()
    successful_runs = 0
    failed_runs = 0

    for idx, s_path in enumerate(scenario_files, 1):
        print(f"\n[{idx}/{total_scenarios}] Processing Scenario: {s_path.name}")
        with open(s_path, "r", encoding="utf-8") as f:
            spec_data = json.load(f)
        spec = ScenarioSpecification(**spec_data)

        # -------------------------------------------------------------------
        # 1. Condition: verifier_guided (Closed-Loop Synthesis)
        # -------------------------------------------------------------------
        print(f"  -> Running [verifier_guided] (Closed-Loop)...", end=" ", flush=True)
        try:
            vg_record = run_scenario(spec, condition="verifier_guided", direct_only=False)
            vg_file = results_dir / f"verifier_guided_{spec.scenario_id}.json"
            save_run(vg_record, vg_file)
            
            # Extract final score for summary print
            score_str = "N/A"
            if vg_record.iterations and vg_record.iterations[-1].get("score") is not None:
                score_str = f"{vg_record.iterations[-1]['score']:.1f}"
            print(f"DONE | State: {vg_record.terminal_state} | Steps: {len(vg_record.iterations)} | Score: {score_str}")
            successful_runs += 1
        except Exception as e:
            print(f"FAILED | Error: {e}")
            failed_runs += 1

        # -------------------------------------------------------------------
        # 2. Condition: baseline_direct (Single-Shot Generation)
        # -------------------------------------------------------------------
        print(f"  -> Running [baseline_direct] (Single-Shot)...", end=" ", flush=True)
        try:
            bd_record = run_scenario(spec, condition="baseline_direct", direct_only=True)
            
            # Post-hoc evaluation of the baseline simulation for direct comparison
            sim_dict = bd_record.iterations[0].get("simulation")
            if sim_dict:
                from models.schemas.simulation import GeneratedSimulation
                sim_obj = GeneratedSimulation(**sim_dict)
                
                # Run through Safety Gate, Verifier, and Scoring Engine
                safety_res = check_safety(sim_obj)
                ver_res = verify_simulation(spec, sim_obj)
                ver_res = ver_res.model_copy(
                    update={
                        "safety_status": safety_res.status,
                        "safety_findings": safety_res.findings,
                    }
                )
                scored_ver = compute_score(ver_res)

                # Attach post-hoc evaluation to iteration record
                bd_record.iterations[0]["safety_result"] = safety_res.model_dump(mode="json")
                bd_record.iterations[0]["verification"] = scored_ver.model_dump(mode="json")
                bd_record.iterations[0]["score"] = scored_ver.overall_score

            bd_file = results_dir / f"baseline_direct_{spec.scenario_id}.json"
            save_run(bd_record, bd_file)

            score_str = "N/A"
            if bd_record.iterations and bd_record.iterations[0].get("score") is not None:
                score_str = f"{bd_record.iterations[0]['score']:.1f}"
            print(f"DONE | State: {bd_record.terminal_state} | Score (Post-Hoc): {score_str}")
            successful_runs += 1
        except Exception as e:
            print(f"FAILED | Error: {e}")
            failed_runs += 1

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"BENCHMARK COMPLETED in {elapsed:.1f}s | Successes: {successful_runs} | Failures: {failed_runs}")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()
