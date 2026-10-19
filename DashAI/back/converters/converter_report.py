"""Helpers to persist the report produced by converter executions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def get_converter_report_path(notebook_path: str | Path, converter_id: int) -> Path:
    """Return the JSON file path used to store a converter execution report."""

    return Path(notebook_path) / "converters" / str(converter_id) / "report.json"


def save_converter_report(
    notebook_path: str | Path, converter_id: int, report: Dict[str, Any]
) -> Path:
    """Persist a JSON-serializable converter report to disk."""

    report_path = get_converter_report_path(notebook_path, converter_id)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return report_path


def load_converter_report(
    notebook_path: str | Path, converter_id: int
) -> Dict[str, Any] | None:
    """Load a converter execution report from disk, if it exists."""

    report_path = get_converter_report_path(notebook_path, converter_id)
    if not report_path.exists():
        return None
    return json.loads(report_path.read_text(encoding="utf-8"))
