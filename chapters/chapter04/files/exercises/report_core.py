"""Exercise 5, file 1 of 3: the pure part.

Expectations and S from data, with no file access and no printing. The recorded run
is read by the wiring, not here, so this file can be tested with four dictionaries.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import bell


def expectations(counts_by_setting: Dict[str, Dict[str, int]]) -> Dict[str, float]:
    """One expectation per setting, from histograms."""
    missing = set(bell.SETTINGS) - set(counts_by_setting)
    if missing:
        raise ValueError(f"missing settings: {sorted(missing)}")
    return {name: bell.expectation_from_counts(counts) for name, counts in counts_by_setting.items()}


def summary(counts_by_setting: Dict[str, Dict[str, int]], shots: int) -> Dict[str, float]:
    """S, its error, the margin and the fraction of the ideal violation."""
    values = expectations(counts_by_setting)
    s_value = bell.chsh(values)
    error = bell.chsh_error(values, shots)
    return {
        "S": s_value,
        "error": error,
        "margin": s_value - bell.CLASSICAL_BOUND,
        "sigma": (s_value - bell.CLASSICAL_BOUND) / error,
        "fraction": (s_value - bell.CLASSICAL_BOUND) / (bell.TSIRELSON_BOUND - bell.CLASSICAL_BOUND),
    }


def rows(result: Dict[str, float]) -> List[Tuple[str, str]]:
    return [
        ("S", f"{result['S']:.4f}"),
        ("1 sigma", f"{result['error']:.4f}"),
        ("margin over 2", f"{result['margin']:+.4f}"),
        ("significance", f"{result['sigma']:.1f} sigma"),
        ("of the ideal violation", f"{result['fraction']:.3f}"),
    ]
