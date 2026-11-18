"""Exercise 4 (break): the decider that never asks whether a classical answer exists.

Run: python3 chapters/chapter20/files/exercises/ex4_classical.py

The first question is the one a reader is most tempted to drop, because the other three
are about the machine and the machine is what the book is about. Without it, a four-qubit
Bernstein-Vazirani run that a laptop answers in microseconds becomes a device candidate,
and on a provider that charges per shot the mistake has an invoice.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, List

from ledger import MAX_DEPTH, MAX_QUBITS, Problem, cases, decide_problem


def decide_without_classical(problem: Problem) -> str:
    """The defect: questions two to four, and the one that mattered left out."""
    usd = problem.price()
    if problem.qubits > MAX_QUBITS or problem.depth > MAX_DEPTH:
        return "wait"
    if not problem.checkable:
        return "simulate"
    if usd > problem.budget_usd:
        return "refuse"
    return "device"


def checks(check: Callable[[bool, str], None]) -> None:
    problems = cases()
    correct = [decide_problem(problem).decision for problem in problems]
    broken = [decide_without_classical(problem) for problem in problems]

    check(correct == ["device", "skip", "wait", "simulate", "refuse", "skip"], "the decider's six answers")
    check(broken == ["device", "device", "wait", "simulate", "refuse", "device"], "the broken one turns two skips into devices")

    check(correct.count("device") == 1, "one device candidate with the question")
    check(broken.count("device") == 3, "and three without it")
    check(correct.count("skip") == 2 and broken.count("skip") == 0, "the skips disappear")

    differing = [problem.name for problem, a, b in zip(problems, correct, broken) if a != b]
    check(differing == ["bv-4-advantage", "maxcut-8"], "exactly the two advantage cases differ")

    check(correct[2] == broken[2], "Shor is deferred either way")
    check(correct[3] == broken[3], "the random circuit is simulated either way")
    check(correct[4] == broken[4], "the IonQ case is refused either way")

    expensive = Problem(
        "bv-advantage-ionq",
        qubits=4,
        depth=10,
        classical="easy",
        checkable=True,
        purpose="advantage",
        provider="ionq",
        shots=2048,
        budget_usd=1000.0,
    )
    check(decide_problem(expensive).decision == "skip", "a classical answer is still skipped on IonQ")
    check(decide_without_classical(expensive) == "device", "the defect buys the run")
    check(abs(decide_problem(expensive).usd - 984.84) < 1e-9, "for 984.84 dollars")
    check(decide_problem(problems[1]).failed.startswith("Does the problem need"), "and the missing question is named")

    check(all(answer in {"device", "skip", "wait", "simulate", "refuse"} for answer in broken), "the defect still returns a decision")
    check(broken == [decide_without_classical(problem) for problem in problems], "deterministically")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
