"""Exercise 5, file 2 of 3: the part that owns the effect.

Formatting only: rows in, one string out. It writes nothing to stdout itself, so
the same string can go to a terminal, a file or a test.
"""

from __future__ import annotations

from typing import List

from report_core import Row


def render_header(title: str, shots: int) -> str:
    return f"{title}\nshots: {shots}\n"


def render_rows(rows: List[Row]) -> str:
    lines = [f"{'outcome':8s}{'real':>10s}{'imag':>10s}{'p':>9s}{'count':>8s}{'freq':>9s}"]
    for label, real, imag, probability, count, frequency in rows:
        lines.append(
            f"{label:8s}{real:10.6f}{imag:10.6f}{probability:9.5f}{count:8d}{frequency:9.5f}"
        )
    return "\n".join(lines) + "\n"


def render_footer(probability_sum: float, count_sum: float, frequency_sum: float) -> str:
    return (
        f"{'sums':8s}{'':10s}{'':10s}{probability_sum:9.5f}"
        f"{int(count_sum):8d}{frequency_sum:9.5f}\n"
    )


def render_report(title: str, shots: int, rows: List[Row], totals: dict) -> str:
    return (
        render_header(title, shots)
        + "\n"
        + render_rows(rows)
        + render_footer(totals["probability"], totals["count"], totals["frequency"])
    )
