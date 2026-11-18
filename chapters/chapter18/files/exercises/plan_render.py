"""Exercise 5, file 2 of 3: rendering."""

from __future__ import annotations

from typing import Dict, List, Tuple


def rows(summary: Dict[str, float], order: List[str]) -> List[Tuple[str, str]]:
    return [
        ("sources", f"{int(summary['rows'])}"),
        ("devices", f"{int(summary['device_rows'])}"),
        ("simulators", f"{int(summary['sim_rows'])}"),
        ("best distance", f"{summary['best']:.4f}"),
        ("worst distance", f"{summary['worst']:.4f}"),
        ("spread", f"{summary['spread']:.4f}"),
    ]


def render(summary: Dict[str, float], order: List[str], title: str, decision: str) -> str:
    if not title:
        raise ValueError("a report needs a title")
    lines = [title, f"{'quantity':16s}{'value':>14s}"]
    for name, value in rows(summary, order):
        lines.append(f"{name:16s}{value:>14s}")
    lines.append("")
    lines.append("ranking:")
    for position, source in enumerate(order, start=1):
        lines.append(f"  {position}. {source}")
    lines.append(f"verdict: {decision}")
    return "\n".join(lines) + "\n"
