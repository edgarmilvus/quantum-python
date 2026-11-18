"""Exercise 5, file 1 of 3: the pure part.

Benchmark rows in, a ranking and a verdict out. No file, no provider, no print.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

from bench import task


def summarise(rows: Sequence[task.Row]) -> Dict[str, float]:
    if len(rows) < 2:
        raise ValueError(f"a ranking needs two rows, got {len(rows)}")
    best = min(rows, key=lambda row: row.tvd)
    worst = max(rows, key=lambda row: row.tvd)
    return {
        "rows": float(len(rows)),
        "best": best.tvd,
        "worst": worst.tvd,
        "ratio": worst.tvd / best.tvd if best.tvd > 0 else float("inf"),
        "spread": worst.tvd - best.tvd,
        "device_rows": float(sum(1 for row in rows if row.kind == "qpu")),
        "sim_rows": float(sum(1 for row in rows if row.kind == "sim")),
    }


def ranking(rows: Sequence[task.Row]) -> List[str]:
    return [row.source for row in sorted(rows, key=lambda row: row.tvd)]


def verdict(summary: Dict[str, float]) -> str:
    """What a reader should take away, in one of four sentences."""
    if summary["device_rows"] == 0:
        return "simulators only: nothing here measures a machine"
    if summary["best"] < 0.005:
        return "an exact source wins and the devices are the story"
    if summary["spread"] > 0.05:
        return "the sources are far apart"
    return "the sources are close together"
