"""Exercise 3 (measure): the margin, in sigmas, from the recorded run.

A violation of 0.54 looks convincing until someone asks how many shots it took. The
answer is four settings at 1024 shots each, and the margin is eleven standard errors.

Run: python3 chapters/chapter04/files/exercises/ex3_margin.py
"""

import pathlib as _pathlib
import json
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import bell

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def measured() -> Dict[str, float]:
    record = json.loads((ROOT / "runs/0007-ibm-chsh/result.json").read_text())
    return {name: bell.expectation_from_counts(c) for name, c in record["counts"].items()}


def margin(expectations: Dict[str, float], shots: int) -> Dict[str, float]:
    value = bell.chsh(expectations)
    error = bell.chsh_error(expectations, shots)
    return {
        "S": value,
        "error": error,
        "margin": value - bell.CLASSICAL_BOUND,
        "sigma": (value - bell.CLASSICAL_BOUND) / error,
        "fraction_of_ideal": (value - bell.CLASSICAL_BOUND) / (bell.TSIRELSON_BOUND - bell.CLASSICAL_BOUND),
    }


def checks(check: Callable[[bool, str], None]) -> None:
    values = measured()
    result = margin(values, 1024)

    check(len(values) == 4, "four settings are read")
    check(abs(result["S"] - 2.541) < 0.01, "S is 2.541")
    check(0.03 < result["error"] < 0.07, "the error is about 0.05")
    check(abs(result["margin"] - 0.541) < 0.01, "the margin is 0.541")
    check(result["sigma"] > 5, "the margin is more than five sigma")
    check(abs(result["fraction_of_ideal"] - 0.653) < 0.01, "65% of the ideal violation survived")
    check(result["S"] < bell.TSIRELSON_BOUND, "the measurement stays under Tsirelson")

    # The same data with more shots would be more significant, at the same margin.
    doubled = margin(values, 4096)
    check(abs(doubled["S"] - result["S"]) < 1e-12, "more shots do not move S")
    check(doubled["sigma"] > result["sigma"], "more shots raise the significance")

    # A margin of zero is not a violation, however many shots.
    flat = {"ab": 0.0, "ab_prime": 0.0, "a_prime_b": 0.0, "a_prime_b_prime": 0.0}
    check(abs(bell.chsh(flat)) < 1e-12, "uncorrelated settings give S = 0")
    half = {name: 0.5 for name in bell.SETTINGS}
    check(abs(bell.chsh(half) - 1.0) < 1e-12, "all settings at 0.5 give S = 1")

    try:
        margin({"ab": 0.5}, 1024)
    except ValueError:
        check(True, "an incomplete set is refused")
    else:
        check(False, "an incomplete set is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
