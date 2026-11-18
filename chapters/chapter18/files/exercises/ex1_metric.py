"""Exercise 1 (repair): a distance that forgets half the ideal.

Run: python3 chapters/chapter18/files/exercises/ex1_metric.py

Summing over the keys the run produced and ignoring the keys the ideal has is the
easiest way to write the metric and the fastest way to make a bad backend look
perfect: a run that only ever produced 000 has no key for 111, so nothing reminds
the code that half the mass is missing.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from bench import task


def tvd_observed_only(counts: Dict[str, int], ideal: Dict[str, float]) -> float:
    """The defect: compare the two distributions on the run's support only.

    Restricting both to the keys the run produced and renormalising both makes the
    comparison self-consistent and wrong: a run that never left 000 has a support of
    one key, and on that key both distributions are one.
    """
    total = sum(counts.values())
    support = set(counts)
    observed = {key: counts[key] / total for key in support}
    restricted = {key: ideal.get(key, 0.0) for key in support}
    mass = sum(restricted.values())
    if mass <= 0:
        raise ValueError("the ideal has no mass on the run's support")
    expected = {key: value / mass for key, value in restricted.items()}
    return 0.5 * sum(abs(observed[key] - expected[key]) for key in support)


def checks(check: Callable[[bool, str], None]) -> None:
    ideal = {"000": 0.5, "111": 0.5}
    perfect = {"000": 2048, "111": 2048}
    half_missing = {"000": 4096}
    skewed = {"000": 3000, "111": 1096}

    check(task.total_variation(perfect, ideal) == 0.0, "the correct metric is zero on a perfect run")
    check(tvd_observed_only(perfect, ideal) == 0.0, "and so is the defect, there")
    check(task.total_variation(skewed, ideal) > 0.1, "a skewed run is far from ideal")

    check(abs(task.total_variation(half_missing, ideal) - 0.5) < 1e-12,
          "a run missing half the ideal is 0.5 away")
    check(abs(tvd_observed_only(half_missing, ideal)) < 1e-12, "the defect calls it perfect")
    check(task.signal(half_missing) == 1.0, "which is why the signal alone is not a metric either")

    three = {"000": 1365, "111": 1365, "001": 1366}
    check(task.total_variation(three, ideal) > 0.3, "a third outcome costs a third of the mass")
    check(abs(tvd_observed_only(three, ideal) - task.total_variation(three, ideal)) < 1e-12,
          "when the run covers both ideal keys the defect is exact, which is why it ships")

    check(tvd_observed_only({"000": 4096}, {"000": 0.25, "111": 0.75}) == 0.0,
          "an ideal row with no mass for a key hides it")

    check(task.total_variation({"000": 1, "111": 1}, ideal) == 0.0, "two shots can still be exact")
    check(abs(task.total_variation({"000": 1}, ideal) - 0.5) < 1e-12,
          "and one outcome is always half the distance")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
