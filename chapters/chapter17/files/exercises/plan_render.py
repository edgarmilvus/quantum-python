"""Exercise 5, file 2 of 3: rendering."""

from __future__ import annotations

from typing import Dict, List, Tuple


def rows(summary: Dict[str, float], control: Dict[str, float]) -> List[Tuple[str, str]]:
    return [
        ("shots", f"{int(summary['shots'])}"),
        ("clean codeword", f"{summary['clean']:.3f}"),
        ("logical error", f"{summary['logical']:.4f}"),
        ("control's error", f"{control['logical']:.4f}"),
        ("control's clean", f"{control['clean']:.3f}"),
    ]


def render(summary: Dict[str, float], control: Dict[str, float], title: str, decision: str) -> str:
    if not title:
        raise ValueError("a report needs a title")
    lines = [title, f"{'quantity':20s}{'value':>14s}"]
    for name, value in rows(summary, control):
        lines.append(f"{name:20s}{value:>14s}")
    lines.append(f"{'verdict':20s}{decision:>14s}")
    return "\n".join(lines) + "\n"
