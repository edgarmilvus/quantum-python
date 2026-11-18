"""Exercise 5, file 2 of 3: rendering.

Rows in, a string out. No arithmetic and no printing of its own.
"""

from __future__ import annotations

from typing import Sequence, Tuple


def render(result_rows: Sequence[Tuple[str, str]], title: str = "query report") -> str:
    lines = [title, f"{'metric':20s}{'value':>14s}"]
    for metric, value in result_rows:
        lines.append(f"{metric:20s}{value:>14s}")
    return "\n".join(lines) + "\n"
