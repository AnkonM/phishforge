"""
server/run_store.py

Persists RunRecords as individual JSON files under runs/, reusing the
existing core.storage.run_writer.save_run/load_run functions verbatim (same
`model_dump_json`/`model_validate_json` format the CLI's --out already
produces). A small sidecar file (runs/_meta.json) tracks two things the
core RunRecord schema has no field for, so it is never touched:
  - which run_ids were imported from evaluation/results/ (vs. created live)
  - which run_ids belong to the same "compare" group
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from core.storage.run_writer import load_run, save_run
from models.schemas.run import RunRecord
from server import config as server_config

_lock = threading.Lock()


def _runs_dir() -> Path:
    # Read dynamically (not cached at import time) so tests can monkeypatch
    # server.config.RUNS_DIR to an isolated tmp directory per test.
    return server_config.RUNS_DIR


def _meta_file() -> Path:
    return _runs_dir() / "_meta.json"


def _run_path(run_id: str) -> Path:
    return _runs_dir() / f"{run_id}.json"


def _load_meta() -> dict:
    meta_file = _meta_file()
    if not meta_file.exists():
        return {"imported_run_ids": [], "compare_groups": {}}
    with open(meta_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_meta(meta: dict) -> None:
    with open(_meta_file(), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def save(record: RunRecord) -> None:
    with _lock:
        save_run(record, _run_path(record.run_id))


def get(run_id: str) -> RunRecord | None:
    path = _run_path(run_id)
    if not path.exists():
        return None
    return load_run(path)


def delete(run_id: str) -> bool:
    path = _run_path(run_id)
    if not path.exists():
        return False
    with _lock:
        path.unlink()
        meta = _load_meta()
        meta["imported_run_ids"] = [r for r in meta.get("imported_run_ids", []) if r != run_id]
        for group_id, ids in list(meta.get("compare_groups", {}).items()):
            if run_id in ids:
                meta["compare_groups"][group_id] = [r for r in ids if r != run_id]
        _save_meta(meta)
    return True


def list_all() -> list[RunRecord]:
    records = []
    for path in sorted(_runs_dir().glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            records.append(load_run(path))
        except Exception:
            continue
    return records


def mark_imported(run_id: str) -> None:
    with _lock:
        meta = _load_meta()
        if run_id not in meta.get("imported_run_ids", []):
            meta.setdefault("imported_run_ids", []).append(run_id)
        _save_meta(meta)


def is_imported(run_id: str) -> bool:
    return run_id in _load_meta().get("imported_run_ids", [])


def imported_ids() -> set[str]:
    return set(_load_meta().get("imported_run_ids", []))


def set_compare_group(group_id: str, run_ids: list[str]) -> None:
    with _lock:
        meta = _load_meta()
        meta.setdefault("compare_groups", {})[group_id] = run_ids
        _save_meta(meta)


def compare_group_for(run_id: str) -> str | None:
    meta = _load_meta()
    for group_id, ids in meta.get("compare_groups", {}).items():
        if run_id in ids:
            return group_id
    return None
