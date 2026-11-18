"""Exercise 3 (measure): what the book's own runs would have cost on a QPU.

Every recorded run in this book was free: IBM's open plan bills runtime, not jobs, and the
simulators are free. This exercise prices the same jobs on a paid QPU, which is the number a
reader needs before designing an experiment.

Run: python3 chapters/chapter11/files/exercises/ex3_cost.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

import providers as p

# case: (circuits, shots per circuit, where it ran)
RUNS = {
    "0001-ibm-fez-bell": (1, 1024, "ibm open plan"),
    "0007-ibm-chsh": (4, 1024, "ibm open plan"),
    "0009-ibm-readout": (4, 4096, "ibm open plan"),
    "0011-ibm-bv": (1, 1024, "ibm open plan"),
    "0013-ibm-grover": (1, 1024, "ibm open plan"),
    "0017-ibm-vqe": (2, 10_000, "ibm open plan"),
}


def cost_on(provider: str, circuits: int, shots: int) -> float:
    return p.PRICES[provider].quote(shots, tasks=circuits)


def table(provider: str = "ionq") -> List[Dict[str, float]]:
    rows = []
    for case, (circuits, shots, where) in RUNS.items():
        rows.append(
            {
                "case": case,
                "circuits": circuits,
                "shots": shots,
                "cost": cost_on(provider, circuits, shots),
                "as_run": 0.0 if where.startswith("ibm") else cost_on(provider, circuits, shots),
            }
        )
    return rows


def total(provider: str = "ionq") -> float:
    return sum(row["cost"] for row in table(provider))


def checks(check: Callable[[bool, str], None]) -> None:
    rows = table("ionq")
    check(len(rows) == 6, "six recorded runs")
    check(sum(row["cost"] for row in rows) > 600, "the whole book's runs cost more than six hundred dollars on a QPU")
    check(total("ionq") < 5000, "and less than five thousand")

    bell = next(row for row in rows if row["case"] == "0001-ibm-fez-bell")
    check(abs(bell["cost"] - 82.22) < 0.01, "the Bell run alone is 82.22")

    vqe = next(row for row in rows if row["case"] == "0017-ibm-vqe")
    check(abs(vqe["cost"] - 1600.6) < 1.0, "the VQE run is 1,600 dollars")
    check(vqe["cost"] > bell["cost"], "because two tallies at ten thousand shots")

    check(total("replay") == 0.0, "replayed, the same runs cost nothing")
    check(total("ibm") == 0.0, "and on the open plan they cost runtime rather than dollars")

    check(cost_on("braket-qpu", 1, 1024) > 1.5, "a Braket QPU job is about two dollars")
    check(cost_on("braket-qpu", 1, 1024) < 2.5, "and not ten")

    check(all(row["cost"] >= 0 for row in rows), "no negative costs")
    check(abs(total("ionq") - sum(cost_on("ionq", r[0], r[1]) for r in RUNS.values())) < 1e-9,
          "the total is the sum of the rows")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
