"""Exercise 3 (measure): what the device's peak is worth, against the ideal.

The simulator says 0.9453. The device returns some number, and the exercise puts an
interval on it and compares it with the ideal and with uniform guessing.

Run: python3 chapters/chapter07/files/exercises/ex3_peak.py
"""

import pathlib as _pathlib
import json
import math
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, Tuple

ROOT = _pathlib.Path(__file__).resolve().parents[4]
Z95 = 1.959963984540054


def standard_error(p: float, shots: int) -> float:
    if not 0.0 <= p <= 1.0 or shots <= 0:
        raise ValueError(f"p in [0, 1] and shots positive, got {p} and {shots}")
    return math.sqrt(p * (1 - p) / shots)


def wilson(count: int, shots: int, z: float = Z95) -> Tuple[float, float]:
    if shots <= 0 or not 0 <= count <= shots:
        raise ValueError(f"bad count {count} of {shots}")
    p = count / shots
    d = 1.0 + z * z / shots
    centre = (p + z * z / (2 * shots)) / d
    half = z * math.sqrt(p * (1 - p) / shots + z * z / (4 * shots * shots)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def load() -> dict:
    return json.loads((ROOT / "runs/0013-ibm-grover/result.json").read_text())


def quality(counts: Dict[str, int], marked: str) -> Dict[str, float]:
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no quality")
    hits = counts.get(marked, 0)
    low, high = wilson(hits, total)
    size = 1 << len(marked)
    return {
        "p": hits / total,
        "error": standard_error(hits / total, total),
        "low": low,
        "high": high,
        "over_uniform": (hits / total) / (1 / size),
        "worst_other": max((v for k, v in counts.items() if k != marked), default=0) / total,
    }


def checks(check: Callable[[bool, str], None]) -> None:
    record = load()
    marked = record["marked_bits"]
    q = quality(record["counts"], marked)

    check(sum(record["counts"].values()) == 1024, "the run has 1024 shots")
    check(0.2 < q["p"] < 0.95, "the marked item comes back between twenty and ninety-five percent")
    check(q["low"] < q["p"] < q["high"], "the interval contains the estimate")
    check(q["over_uniform"] > 4, "the peak beats uniform guessing by more than four times")
    check(q["worst_other"] < 0.5, "no other outcome takes half the shots")
    check(q["p"] < record["ideal_probability"] + 1e-9, "the device does not beat the simulator")
    check(q["p"] < record["ideal_probability"], "the device loses something to noise")
    check(record["transpiled_depth"] > 100, "the circuit is deep: over a hundred layers")

    doubled = quality({k: v * 4 for k, v in record["counts"].items()}, marked)
    check(abs(doubled["p"] - q["p"]) < 1e-12, "four times the shots do not move the estimate")

    try:
        quality({}, marked)
    except ValueError:
        check(True, "an empty histogram is refused")
    else:
        check(False, "an empty histogram is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
