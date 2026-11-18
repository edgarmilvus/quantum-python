"""Exercise 5, file 2 of 3: rendering.

Rows in, a string out. No arithmetic, no file access, no printing of its own.
"""

from __future__ import annotations

from typing import Sequence, Tuple


def render(result_rows: Sequence[Tuple[str, str]], title: str = "CHSH report") -> str:
    lines = [title, f"{'metric':24s}{'value':>12s}"]
    for metric, value in result_rows:
        lines.append(f"{metric:24s}{value:>12s}")
    return "\n".join(lines) + "\n"
