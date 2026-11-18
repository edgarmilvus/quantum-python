"""Exercise 2 (extend): what the six cases cost together.

Run: python3 chapters/chapter20/files/exercises/ex2_cases.py

The decider answers one problem at a time. A reader with a Monday has six, and the
question becomes what the batch costs and which case is the one that breaks the budget.
The extension is an aggregate with a named culprit, because "over budget" without a name
is a refusal a reader cannot act on.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from dataclasses import dataclass
from typing import Callable, Sequence

from ledger import Problem, cases, decide_problem


@dataclass(frozen=True)
class Budget:
    allowed: bool
    usd: float
    worst: str
    reason: str = ""


def total_price(problems: Sequence[Problem]) -> float:
    return sum(decide_problem(problem).usd for problem in problems)


def affordable(problems: Sequence[Problem], budget_usd: float) -> Budget:
    if budget_usd < 0:
        raise ValueError(f"a budget is non-negative, got {budget_usd}")
    priced = [(decide_problem(problem).usd, problem.name) for problem in problems]
    usd = sum(price for price, _ in priced)
    if usd <= budget_usd:
        return Budget(True, usd, "")
    price, name = max(priced, key=lambda pair: pair[0])
    return Budget(False, usd, name, f"{name} alone is {price:.2f} USD and the batch is {usd:.2f}")


def checks(check: Callable[[bool, str], None]) -> None:
    problems = cases()

    check(abs(total_price(problems) - 984.84) < 1e-9, "the six cases cost 984.84")
    check(total_price([]) == 0.0, "an empty batch costs nothing")
    check(total_price(problems[:1]) == 0.0, "the IBM demo is free")
    check(abs(total_price(problems[4:5]) - 984.84) < 1e-9, "the IonQ case is the whole bill")

    verdict = affordable(problems, 5.0)
    check(not verdict.allowed, "the batch is refused at five dollars")
    check(verdict.worst == "ionq-demo", "and the culprit is named")
    check("984.84" in verdict.reason, "with the price in the message")

    generous = affordable(problems, 1000.0)
    check(generous.allowed, "a thousand dollars allows it")
    check(generous.worst == "", "and there is no culprit")

    check(affordable([], 0.0).allowed, "an empty batch is allowed by a zero budget")
    check(affordable(problems[1:2], 0.0).allowed, "the skip case is free")

    for bad in (-1.0, -100.0):
        try:
            affordable(problems, bad)
        except ValueError:
            check(True, f"a budget of {bad} is refused")
        else:
            check(False, f"a budget of {bad} is refused")

    check(total_price(problems) == sum(problem.price() for problem in problems), "the total is the sum of the prices")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
