"""
scripts/seed_runs.py

One-time idempotent import of the 24 real benchmark RunRecords already in
evaluation/results/*.json (12 verifier_guided + 12 baseline_direct, from
real Gemini runs) into runs/, so Runs/Dashboard have real data immediately
without needing to run anything first. Marks each as "imported" in the
server's sidecar metadata (never alters the RunRecord itself). Safe to
run multiple times -- skips any run_id already present.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.storage.run_writer import load_run  # noqa: E402
from server import run_store  # noqa: E402
from server.config import EVAL_RESULTS_DIR  # noqa: E402


def main() -> None:
    if not EVAL_RESULTS_DIR.exists():
        print(f"No evaluation results directory at {EVAL_RESULTS_DIR}; nothing to seed.")
        return

    imported = 0
    skipped = 0
    for path in sorted(EVAL_RESULTS_DIR.glob("*.json")):
        if path.name.startswith("summary_metrics"):
            continue
        try:
            record = load_run(path)
        except Exception as exc:  # noqa: BLE001
            print(f"  skip (unparseable): {path.name}: {exc}")
            continue

        if run_store.get(record.run_id) is not None:
            skipped += 1
            continue

        run_store.save(record)
        run_store.mark_imported(record.run_id)
        imported += 1
        print(f"  imported: {path.name} -> run_id={record.run_id} ({record.condition}, {record.terminal_state})")

    print(f"\nSeed complete: {imported} imported, {skipped} already present.")


if __name__ == "__main__":
    main()
