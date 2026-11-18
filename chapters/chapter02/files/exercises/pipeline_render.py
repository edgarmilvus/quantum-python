"""Exercise 5, file 2 of 3: rendering only.

Rows in, one string out. No arithmetic, no sampling, no stdout of its own.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple


def render_table(rows: Sequence[Tuple[str, float]]) -> str:
    lines = [f"{'state':8s}{'probability':>12s}"]
    for label, probability in rows:
        lines.append(f"{label:8s}{probability:12.6f}")
    return "\n".join(lines) + "\n"


def render_title(title: str, wires: int) -> str:
    return f"{title}\n{wires} wires\n"


def render(state_rows: Sequence[Tuple[str, float]], title: str = "pipeline") -> str:
    wires = len(str(state_rows[0][0])) if state_rows else 0
    return render_title(title, wires) + render_table(state_rows)
