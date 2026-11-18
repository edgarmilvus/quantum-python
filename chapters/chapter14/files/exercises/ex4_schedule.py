"""Exercise 4 (break): two ways to freeze in the wrong basin.

Run: python3 chapters/chapter14/files/exercises/ex4_schedule.py

A schedule has a length and a starting temperature, and both can be wrong. One
sweep gives the annealer no chance to move, and a cold start removes the energy
it would need to leave the basin it began in. The two failures look different in
the output and are the same mistake: the state stopped exploring before it had
found the valley.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

from anneal import instances, sampler


def outcome(sweeps: int, hot: float = 4.0, reads: int = 200, seed: int = 11) -> Dict[str, float]:
    coupling = instances.spin_glass()
    optimum = sampler.Exact({}, coupling).sample().best()[0]
    result = sampler.Annealer({}, coupling, 0.0, sweeps=sweeps, hot=hot, seed=seed).sample(reads)
    return {
        "success": sampler.success_rate(result, optimum),
        "best": result.best()[0],
        "optimum": optimum,
        "acceptance": result.info["acceptance"],
        "distinct": float(result.unique()),
    }


def curve(sweeps: List[int]) -> List[Dict[str, float]]:
    return [{"sweeps": float(value), **outcome(value)} for value in sweeps]


def checks(check: Callable[[bool, str], None]) -> None:
    one = outcome(1)
    ten = outcome(10)
    hundred = outcome(100)

    check(one["success"] < 0.05, "one sweep finds the optimum less than 5% of the time")
    check(one["acceptance"] > 0.3, "because it accepts a third of its moves and never settles")
    check(ten["success"] > 0.7, "ten sweeps finds it more than 70% of the time")
    check(hundred["success"] > 0.85, "and a hundred more than 85%")

    check(ten["success"] > one["success"], "more sweeps is better")
    check(hundred["acceptance"] < ten["acceptance"], "with a lower acceptance rate, because it cools further")

    cold = outcome(100, hot=0.2)
    warm = outcome(100, hot=4.0)
    check(cold["success"] < warm["success"], "a cold start does worse than a hot one")
    check(warm["success"] - cold["success"] > 0.2, "and by more than twenty points")
    check(cold["acceptance"] < warm["acceptance"], "because it accepts fewer moves early on")

    rows = curve([1, 2, 3, 5, 10])
    check(len(rows) == 5, "five schedule lengths")
    check(rows[0]["success"] < rows[-1]["success"], "and the first is worse than the last")
    check(all(row["best"] >= row["optimum"] - 1e-9 for row in rows), "no run beats the optimum")

    check(abs(one["optimum"] + 24.0) < 1e-9, "the instance's optimum is -24")

    for bad in (0, -5):
        try:
            sampler.Annealer({}, instances.spin_glass(), 0.0, sweeps=bad)
        except ValueError:
            check(True, f"{bad} sweeps is refused")
        else:
            check(False, f"{bad} sweeps is refused")

    for bad in (0.0, -1.0):
        try:
            sampler.Annealer({}, instances.spin_glass(), 0.0, hot=bad)
        except ValueError:
            check(True, f"a starting temperature of {bad} is refused")
        else:
            check(False, f"a starting temperature of {bad} is refused")

    try:
        sampler.Annealer({}, instances.spin_glass(), 0.0, hot=0.1, cold=1.0)
    except ValueError:
        check(True, "a schedule that heats instead of cooling is refused")
    else:
        check(False, "a schedule that heats instead of cooling is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
