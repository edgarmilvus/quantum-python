"""Exercise 5, file 2 of 3: rendering."""

from __future__ import annotations

from typing import Dict, List, Tuple


def rows(summary: Dict[str, float]) -> List[Tuple[str, str]]:
    return [
        ("shots", f"{int(summary['shots'])}"),
        ("raw peak", f"{summary['raw']:.4f}"),
        ("corrected peak", f"{summary['corrected']:.4f}"),
        ("gain", f"{summary['gain']:+.4f}"),
    ]


def render(summary: Dict[str, float], title: str, decision: str) -> str:
    if not title:
        raise ValueError("a report needs a title")
    lines = [title, f"{'quantity':18s}{'value':>12s}"]
    for name, value in rows(summary):
        lines.append(f"{name:18s}{value:>12s}")
    lines.append(f"{'verdict':18s}{decision:>12s}")
    return "\n".join(lines) + "\n"
