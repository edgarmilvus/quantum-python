"""Exercise 5, file 2 of 3: rendering.

A summary in, a table out. No arithmetic, no sampler, no printing.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


def rows(summary: Dict[str, float], target_reads: int) -> List[Tuple[str, str]]:
    return [
        ("best energy", f"{summary['best']:.3f}"),
        ("optimum", f"{summary['optimum']:.3f}"),
        ("gap", f"{summary['gap']:+.3f}"),
        ("reads", f"{int(summary['reads'])}"),
        ("successful reads", f"{summary['success']:.1%}"),
        ("distinct samples", f"{int(summary['distinct'])}"),
        ("reads for 95%", f"{target_reads}"),
    ]


def render(summary: Dict[str, float], title: str, decision: str, target_reads: int) -> str:
    if not title:
        raise ValueError("a report needs a title")
    lines = [title, f"{'quantity':22s}{'value':>12s}"]
    for name, value in rows(summary, target_reads):
        lines.append(f"{name:22s}{value:>12s}")
    lines.append(f"{'verdict':22s}{decision:>12s}")
    return "\n".join(lines) + "\n"
