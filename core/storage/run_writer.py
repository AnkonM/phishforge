"""
core/storage/run_writer.py

Persistence layer for PhishForge run artifacts.
Saves and loads RunRecord schemas to/from plain JSON files.

Source of truth: Document B v2 §6.2.

Architecture rules (Document B v2 §7):
  - No print() statements.
  - No database coupling (SQLite is Future Scope in v2 §16).
  - Uses standard UTF-8 JSON serialization.
"""

from __future__ import annotations

import os
from pathlib import Path

from models.schemas.run import RunRecord


def save_run(record: RunRecord, path: str | Path) -> None:
    """
    Serialize and save a RunRecord to disk as a JSON file.

    Parameters
    ----------
    record:
        The completed RunRecord to persist.
    path:
        Destination file path. Parent directories are created automatically.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    json_data = record.model_dump_json(indent=2)
    path.write_text(json_data, encoding="utf-8")


def load_run(path: str | Path) -> RunRecord:
    """
    Load and validate a RunRecord from disk.

    Parameters
    ----------
    path:
        Source JSON file path.

    Returns
    -------
    RunRecord
        Validated RunRecord instance.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    pydantic.ValidationError
        If the JSON data does not match the RunRecord schema.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Run record file not found: {path}")
    json_data = path.read_text(encoding="utf-8")
    return RunRecord.model_validate_json(json_data)
