"""Exercise 5, file 2 of 3: rendering the memo."""

from __future__ import annotations

from typing import Dict, List, Tuple


def rows(summary: Dict) -> List[Tuple[str, str]]:
    return [
        ("shots", f"{summary['shots']}"),
        ("dynamic", f"{summary['fidelity']['dynamic']:.4f}"),
        ("postselect", f"{summary['fidelity']['postselect']:.4f}"),
        ("uncorrected", f"{summary['fidelity']['uncorrected']:.4f}"),
        ("correction", f"{summary['gap']:+.4f}"),
    ]


def render(summary: Dict, sentence: str, title: str = "Teleportation") -> str:
    if not title:
        raise ValueError("a memo needs a title")
    if not sentence:
        raise ValueError("a memo needs a sentence")
    lines = [title, f"{'quantity':14s}{'value':>10s}"]
    for name, value in rows(summary):
        lines.append(f"{name:14s}{value:>10s}")
    lines.append("")
    lines.append(sentence)
    return "\n".join(lines) + "\n"
