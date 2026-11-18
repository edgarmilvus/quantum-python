"""Exercise 3 (measure): what the device's answer is worth.

The recorded run returned the secret 965 times out of 1024. That is an estimate, and the
exercise puts an interval on it and compares it with the ideal.

Run: python3 chapters/chapter06/files/exercises/ex3_confidence.py
"""

import pathlib as _pathlib
import json
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))
import math
from typing import Callable, Dict, Tuple

Z95 = 1.959963984540054


def standard_error(p: float, shots: int) -> float:
    if not 0.0 <= p <= 1.0 or shots <= 0:
        raise ValueError(f"p in [0, 1] and shots positive, got {p} and {shots}")
    return math.sqrt(p * (1 - p) / shots)


def wilson(count: int, shots: int, z: float = Z95) -> Tuple[float, float]:
    """The interval from chapter 5, kept here so the exercise stands alone."""
    if shots <= 0 or not 0 <= count <= shots:
        raise ValueError(f"bad count {count} of {shots}")
    p = count / shots
    denominator = 1.0 + z * z / shots
    centre = (p + z * z / (2 * shots)) / denominator
    half = z * math.sqrt(p * (1 - p) / shots + z * z / (4 * shots * shots)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def interval_width(count: int, shots: int, z: float = Z95) -> float:
    low, high = wilson(count, shots, z)
    return high - low

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def load() -> dict:
    return json.loads((ROOT / "runs/0011-ibm-bv/result.json").read_text())


def answer_quality(counts: Dict[str, int], secret: str) -> Dict[str, float]:
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no quality")
    hits = counts.get(secret, 0)
    low, high = wilson(hits, total)
    return {
        "p": hits / total,
        "error": standard_error(hits / total, total),
        "low": low,
        "high": high,
        "width": interval_width(hits, total),
        "worst_other": max((v for k, v in counts.items() if k != secret), default=0) / total,
    }


def checks(check: Callable[[bool, str], None]) -> None:
    record = load()
    secret = record["secret_bits"]
    quality = answer_quality(record["counts"], secret)

    check(abs(quality["p"] - 0.9424) < 1e-4, "the secret came back 94.2% of the time")
    check(0.005 < quality["error"] < 0.01, "the standard error is about 0.7 percentage points")
    check(quality["low"] < quality["p"] < quality["high"], "the interval contains the estimate")
    check(quality["width"] < 0.05, "the interval is under five points wide")
    check(quality["p"] > 0.9, "the answer is unambiguous")
    check(quality["worst_other"] < 0.05, "no other outcome exceeds five percent")

    # Four times the shots would halve the width, at the same rate.
    doubled = answer_quality({secret: 3860, "001": 100, "100": 108, "000": 20, "111": 8}, secret)
    check(abs(doubled["p"] - 0.9424) < 0.01, "the same rate at four times the shots")
    check(doubled["width"] < quality["width"], "and a narrower interval")

    try:
        answer_quality({}, "101")
    except ValueError:
        check(True, "an empty histogram is refused")
    else:
        check(False, "an empty histogram is refused")

    check(quality["p"] - 3 * quality["error"] > 0.9,
          "the answer is more than three standard errors from the classical answer")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
