"""Exercise 5, file 2 of 3: rendering.

A summary in, a table out. No arithmetic and no printing of its own.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


def rows(summary: Dict[str, float]) -> List[Tuple[str, str]]:
    return [
        ("penalty", f"{summary['penalty']:.3f}"),
        ("train accuracy", f"{summary['train accuracy']:.3f}"),
        ("test accuracy", f"{summary['test accuracy']:.3f}"),
        ("kernel off-diagonal", f"{summary['off diagonal']:.3f}"),
        ("condition number", f"{summary['condition']:.1f}"),
    ]


def render(summary: Dict[str, float], title: str, decision: str) -> str:
    if not title:
        raise ValueError("a report needs a title")
    lines = [title, f"{'quantity':22s}{'value':>12s}"]
    for name, value in rows(summary):
        lines.append(f"{name:22s}{value:>12s}")
    lines.append(f"{'verdict':22s}{decision:>12s}")
    return "\n".join(lines) + "\n"
