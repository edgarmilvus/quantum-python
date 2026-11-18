"""Exercise 5, file 1 of 3: the pure part.

A task and a record in, the four numbers a report owes out. No file, no provider,
no print.
"""

from __future__ import annotations

from typing import Dict

from pipe import run, spec


def summarise(task: spec.Task, record: Dict) -> Dict[str, float]:
    if record.get("secret") != task.secret:
        raise ValueError(f"the record's secret {record.get('secret')} is not the task's {task.secret}")
    counts = record.get("counts") or {}
    if not counts:
        raise ValueError("the record has no counts")
    model = run.readout(record)
    corrected = run.correct(counts, model)
    raw_key, raw_share = run.top({key: value / sum(counts.values()) for key, value in counts.items()})
    fixed_key, fixed_share = run.top(corrected)
    return {
        "shots": float(record["shots"]),
        "raw": raw_share,
        "corrected": fixed_share,
        "ok": 1.0 if fixed_key == task.secret else 0.0,
        "gain": fixed_share - raw_share,
    }


def verdict(summary: Dict[str, float]) -> str:
    """Four sentences, because the peak, the correction and the answer are separate."""
    if summary["ok"] and summary["gain"] > 0.01:
        return "recovered, and the correction mattered"
    if summary["ok"]:
        return "recovered, and the correction was cosmetic"
    return "not recovered"
