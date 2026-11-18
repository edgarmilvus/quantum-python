"""Exercise 5, file 2 of 3: rendering.

Rows in, a string out. No arithmetic and no printing of its own.
"""

from __future__ import annotations

from typing import Sequence, Tuple


def render(result_rows: Sequence[Tuple[str, str]], title: str = "readout report") -> str:
    lines = [title, f"{'metric':18s}{'value':>10s}"]
    for metric, value in rows_of(result_rows):
        lines.append(f"{metric:18s}{value:>10s}")
    return "\n".join(lines) + "\n"


def rows_of(result_rows: Sequence[Tuple[str, str]]):
    return list(result_rows)
