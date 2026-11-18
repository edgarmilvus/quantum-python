"""Exercise 2 (extend): two more metrics, and what each one is for.

Run: python3 chapters/chapter18/files/exercises/ex2_signal.py

The total variation is the number to report; the signal is the share of shots on
the outcomes the circuit was built for, which is easier to explain; the Hellinger
distance punishes small probabilities less and is what a statistician would use on
a distribution with many near-zero entries.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

from bench import task


def ranked(runs: Dict[str, Dict[str, int]]) -> List[str]:
    """Sources ordered by total variation, best first."""
    ideal = task.ideal_distribution(3)
    return sorted(runs, key=lambda name: task.total_variation(runs[name], ideal))


def checks(check: Callable[[bool, str], None]) -> None:
    ideal = task.ideal_distribution(3)
    runs = {
        "clean": {"000": 2040, "111": 2040, "001": 16},
        "leaky": {"000": 1900, "111": 1900, "001": 100, "010": 96},
        "broken": {"000": 1200, "111": 1400, "001": 400, "010": 400, "100": 696},
    }

    order = ranked(runs)
    check(order == ["clean", "leaky", "broken"], "the ranking is the one the eye expects")

    for name, counts in runs.items():
        check(0 <= task.total_variation(counts, ideal) <= 1, f"{name}'s distance is a fraction")
        check(0 <= task.hellinger(counts, ideal) <= 1, f"{name}'s hellinger is a fraction")
        check(0 <= task.signal(counts) <= 1, f"{name}'s signal is a fraction")

    check(task.signal(runs["clean"]) > 0.99, "a clean run keeps almost all its signal")
    check(task.signal(runs["broken"]) < 0.65, "a broken one loses a third of it")

    tvd_clean = task.total_variation(runs["clean"], ideal)
    tvd_leaky = task.total_variation(runs["leaky"], ideal)
    hel_clean = task.hellinger(runs["clean"], ideal)
    hel_leaky = task.hellinger(runs["leaky"], ideal)
    check(hel_leaky > hel_clean, "hellinger orders them the same way")
    check((tvd_leaky / max(tvd_clean, 1e-9)) > (hel_leaky / max(hel_clean, 1e-9)),
          "but it compresses the gap, because it penalises small mass less")

    check(abs(task.signal(runs["clean"]) - (runs["clean"]["000"] + runs["clean"]["111"]) / 4096) < 1e-12,
          "the signal is the two-outcome share by definition")
    check(task.signal({"000": 4096}) == 1.0, "a run with no leak has signal one")
    check(task.signal({"001": 4096}) == 0.0, "and a run on the wrong outcomes has none")

    check(task.ghz_ops(2) == [("h", (0,)), ("cx", (0, 1))], "a two-qubit GHZ is one CX")
    check(task.ideal_distribution(2) == {"00": 0.5, "11": 0.5}, "with its own ideal")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
