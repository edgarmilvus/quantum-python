"""Exercise 5, file 2 of 3: rendering."""

from __future__ import annotations

from typing import Dict, List, Tuple


def rows(summary: Dict[str, float]) -> List[Tuple[str, str]]:
    return [
        ("shots", f"{int(summary['shots'])}"),
        ("physical rate", f"{summary['physical']:.4f}"),
        ("logical rate", f"{summary['logical']:.4f}"),
        ("95% interval", f"{summary['low']:.4f} to {summary['high']:.4f}"),
        ("improvement", f"{summary['physical'] / summary['logical']:.1f}x" if summary["logical"] > 0 else "better than 1e3"),
    ]


def render(summary: Dict[str, float], title: str, decision: str) -> str:
    if not title:
        raise ValueError("a report needs a title")
    lines = [title, f"{'quantity':18s}{'value':>20s}"]
    for name, value in rows(summary):
        lines.append(f"{name:18s}{value:>20s}")
    lines.append(f"{'verdict':18s}{decision:>20s}")
    return "\n".join(lines) + "\n"
