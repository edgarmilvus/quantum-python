"""What a task will cost before it runs, and whether the budget allows it.

The estimate is four numbers and a verdict: circuits, shots, seconds of runtime and
dollars. The verdict is the guard, and it refuses in the two cases a reader meets
first: the price is over the budget, or the provider would need a key that is not set.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .spec import KNOWN, Task

# Measured on this book's account: six circuits of this size cost about four seconds.
SECONDS_PER_CIRCUIT = 4.0 / 6.0


@dataclass(frozen=True)
class Estimate:
    task: str
    circuits: int
    shots: int
    seconds: float
    usd: float
    allowed: bool
    reason: str = ""

    def report(self) -> str:
        verdict = "allowed" if self.allowed else f"refused: {self.reason}"
        return (
            f"{self.task:24s}{self.circuits:4d} circuits{self.shots:8d} shots"
            f"{self.seconds:8.1f} s{self.usd:9.2f} USD   {verdict}"
        )


def price(provider: str, circuits: int, shots: int) -> float:
    if provider not in KNOWN:
        raise KeyError(f"no price for {provider!r}; known: {sorted(KNOWN)}")
    if circuits < 1 or shots < 1:
        raise ValueError(f"a run needs at least one circuit and one shot, got {circuits} and {shots}")
    per_task, per_shot = KNOWN[provider]
    return per_task * circuits + per_shot * circuits * shots


def estimate(task: Task, key_present: Optional[bool] = None) -> Estimate:
    """The four numbers and the verdict, with the two refusals the pipeline applies."""
    usd = price(task.provider, task.circuits, task.shots)
    seconds = task.circuits * SECONDS_PER_CIRCUIT
    if usd > task.budget_usd:
        return Estimate(task.name, task.circuits, task.shots, seconds, usd, False,
                        f"{usd:.2f} USD is over the {task.budget_usd:.2f} budget")
    if key_present is False:
        return Estimate(task.name, task.circuits, task.shots, seconds, usd, False,
                        f"{task.provider} needs a key that is not set")
    return Estimate(task.name, task.circuits, task.shots, seconds, usd, True)


def cheapest(task: Task) -> str:
    """The provider that would run this task for the least money."""
    prices = {name: price(name, task.circuits, task.shots) for name in KNOWN}
    return min(prices, key=lambda name: prices[name])
