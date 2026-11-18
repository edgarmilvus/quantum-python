"""Exercise 5, file 2 of 3: rendering.

A summary in, a table out. No arithmetic, no graph, no printing.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


def rows(summary: Dict[str, float]) -> List[Tuple[str, str]]:
    return [
        ("layers", f"{int(summary['layers'])}"),
        ("expected cut", f"{summary['mean']:.4f}"),
        ("optimum", f"{summary['optimum']:.4f}"),
        ("ratio", f"{summary['ratio']:.4f}"),
        ("uniform guess", f"{summary['uniform']:.4f}"),
        ("most likely assignment", format(int(summary["best"]), "04b")),
        ("its probability", f"{summary['best probability']:.4f}"),
        ("its cut", f"{summary['best cut']:.4f}"),
    ]


def render(summary: Dict[str, float], title: str, decision: str) -> str:
    if not title:
        raise ValueError("a report needs a title")
    lines = [title, f"{'quantity':24s}{'value':>12s}"]
    for name, value in rows(summary):
        lines.append(f"{name:24s}{value:>12s}")
    lines.append(f"{'verdict':24s}{decision:>12s}")
    return "\n".join(lines) + "\n"
