"""Exercise 5, file 2 of 3: rendering.

A summary in, a table out. No arithmetic and no printing of its own, so the
report can be tested by comparing two strings.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple


def rows(summary: Dict[str, float]) -> List[Tuple[str, str]]:
    return [
        ("raw S", f"{summary['raw']:.4f}"),
        ("readout corrected", f"{summary['corrected']:.4f}"),
        ("closed by readout", f"{summary['closed']:.1%}"),
        ("extrapolated", f"{summary['extrapolated']:.4f}"),
        ("error at scale 0", f"{summary['sigma']:.4f}"),
        ("remaining gap", f"{summary['remaining']:+.4f}"),
        ("distance", f"{summary['z']:+.1f} sigma"),
        ("ideal", f"{summary['ideal']:.4f}"),
    ]


def render(summary: Dict[str, float], title: str, decision: str) -> str:
    if not title:
        raise ValueError("a report needs a title")
    lines = [title, f"{'stage':22s}{'value':>12s}"]
    for name, value in rows(summary):
        lines.append(f"{name:22s}{value:>12s}")
    lines.append(f"{'verdict':22s}{decision:>12s}")
    return "\n".join(lines) + "\n"
