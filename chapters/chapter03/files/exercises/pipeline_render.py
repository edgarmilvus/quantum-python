"""Exercise 5, file 2 of 3: rendering.

Rows in, a string out. No arithmetic, no printing, no knowledge of circuits.
"""

from __future__ import annotations

from typing import Sequence, Tuple


def render(rows: Sequence[Tuple[str, str, str]], title: str = "compilation report") -> str:
    lines = [title, f"{'circuit':14s}{'metric':10s}{'value':>14s}"]
    for circuit, metric, value in rows:
        lines.append(f"{circuit:14s}{metric:10s}{value:>14s}")
    return "\n".join(lines) + "\n"
