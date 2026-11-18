"""Exercise 5, file 2 of 3: rendering.

Rows in, a string out. No arithmetic and no printing of its own.
"""

from __future__ import annotations

from typing import Dict, Sequence, Tuple


def rows(summary: Dict[str, float]) -> Sequence[Tuple[str, str]]:
    return [
        ("shots", str(int(summary["shots"]))),
        ("top outcome", str(summary["top"])),
        ("its frequency", f"{summary['frequency']:.4f}"),
        ("expected outcome", f"{summary['expected']:.4f}"),
        ("correct", "yes" if summary["correct"] else "no"),
        ("outcomes seen", str(int(summary["outcomes"]))),
    ]


def render(summary: Dict[str, float], title: str) -> str:
    lines = [title, f"{'metric':20s}{'value':>12s}"]
    for metric, value in rows(summary):
        lines.append(f"{metric:20s}{value:>12s}")
    return "\n".join(lines) + "\n"
