"""The benchmark: one task, several backends, one distance."""

from . import sources, task
from .task import Row, hellinger, ideal_distribution, noise_floor, signal, table, total_variation

__all__ = [
    "Row",
    "hellinger",
    "ideal_distribution",
    "noise_floor",
    "signal",
    "sources",
    "table",
    "task",
    "total_variation",
]
