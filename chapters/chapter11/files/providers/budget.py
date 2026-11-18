"""What a job costs before it runs, and a guard that refuses to overspend.

Prices are per task and per shot, in dollars, from the providers' published pages in
November 2026. They are the book's constants, not a forecast.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .base import Backend, BackendError


@dataclass(frozen=True)
class Price:
    provider: str
    per_task: float
    per_shot: float
    note: str = ""

    def quote(self, shots: int, tasks: int = 1) -> float:
        if shots <= 0 or tasks <= 0:
            raise ValueError(f"shots and tasks must be positive, got {shots} and {tasks}")
        return tasks * self.per_task + tasks * shots * self.per_shot


PRICES: Dict[str, Price] = {
    "ibm": Price("ibm", 0.0, 0.0, "Open Plan: minutes of runtime, not billed per job"),
    "ionq": Price("ionq", 0.30, 0.08, "per task plus per shot, QPU only"),
    "ionq-simulator": Price("ionq-simulator", 0.0, 0.0, "free"),
    "braket-simulator": Price("braket-simulator", 0.0, 0.0, "one free hour per month"),
    "braket-qpu": Price("braket-qpu", 0.30, 0.0016, "IQM Emerald, the cheapest per shot"),
    "azure": Price("azure", 0.0, 0.0, "credits, not dollars"),
    "qbraid": Price("qbraid", 0.0, 0.0, "simulators free; a QPU passes the vendor's price through"),
    "replay": Price("replay", 0.0, 0.0, "no machine involved"),
}


@dataclass
class Ledger:
    """A running total with a ceiling, so a loop cannot spend by accident."""

    cap_usd: float = 5.0
    spent_usd: float = 0.0
    entries: List[Tuple[str, int, float]] = field(default_factory=list)
    live: bool = False

    def quote(self, provider: str, shots: int, tasks: int = 1) -> float:
        if provider not in PRICES:
            raise BackendError(f"no price for {provider!r}; known: {sorted(PRICES)}")
        return PRICES[provider].quote(shots, tasks)

    def authorise(self, backend: Backend, shots: int, tasks: int = 1) -> float:
        """Return the cost and refuse if it would cross the cap or live is off."""
        cost = self.quote(backend.provider, shots, tasks)
        if not self.live and not _is_replay(backend):
            raise BackendError(
                f"{backend.provider} would spend {cost:.2f} USD and live mode is off; "
                f"set QUANTUM_LIVE=1 to allow it"
            )
        if self.spent_usd + cost > self.cap_usd:
            raise BackendError(
                f"{backend.provider} would take the total to {self.spent_usd + cost:.2f} USD, "
                f"over the {self.cap_usd:.2f} cap"
            )
        return cost

    def commit(self, backend: Backend, shots: int, tasks: int = 1) -> float:
        cost = self.authorise(backend, shots, tasks)
        self.spent_usd += cost
        self.entries.append((backend.provider, shots, cost))
        return cost

    def report(self) -> str:
        if not self.entries:
            return "nothing spent"
        lines = [f"{provider:18s}{shots:>8d} shots  {cost:8.4f} USD" for provider, shots, cost in self.entries]
        lines.append(f"{'total':18s}{'':>8s}  {self.spent_usd:8.4f} USD of {self.cap_usd:.2f}")
        return "\n".join(lines)


def _is_replay(backend: Backend) -> bool:
    from .replay import Replay

    return isinstance(backend, Replay)
