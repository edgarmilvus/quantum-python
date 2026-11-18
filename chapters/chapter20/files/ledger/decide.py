"""Four questions between a problem and a run.

The decider is the chapter's answer to "what should I do on Monday". It takes a problem
described in the terms the book has used for nineteen chapters — qubits, depth, whether a
classical method already answers it, whether the answer can be checked, whether the point
is to learn or to claim an advantage, and the budget — and returns one of five decisions
with the question that decided it.

The order is the argument. A problem that a classical program answers is skipped before
anyone asks about the machine; a circuit that does not fit is deferred before anyone asks
about the price; a result that cannot be checked is simulated before it is believed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# The largest machine and the deepest circuit the book actually ran, rounded.
MAX_QUBITS = 156
MAX_DEPTH = 100

PRICES: Dict[str, Tuple[float, float]] = {
    "local": (0.0, 0.0),
    "ibm": (0.0, 0.0),
    "qbraid": (0.0, 0.0),
    "ionq": (0.30, 0.08),
    "braket-iqm": (0.30, 0.0016),
}


@dataclass(frozen=True)
class Problem:
    name: str
    qubits: int
    depth: int
    classical: str  # "easy" or "hard"
    checkable: bool
    purpose: str  # "learn" or "advantage"
    provider: str = "ibm"
    shots: int = 2048
    budget_usd: float = 5.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a problem needs a name")
        if self.qubits < 1:
            raise ValueError(f"qubits are positive, got {self.qubits}")
        if self.depth < 1:
            raise ValueError(f"depth is positive, got {self.depth}")
        if self.classical not in ("easy", "hard"):
            raise ValueError(f"classical is 'easy' or 'hard', got {self.classical!r}")
        if self.purpose not in ("learn", "advantage"):
            raise ValueError(f"purpose is 'learn' or 'advantage', got {self.purpose!r}")
        if self.provider not in PRICES:
            raise ValueError(f"unknown provider {self.provider!r}; known: {sorted(PRICES)}")
        if self.shots < 1:
            raise ValueError(f"shots are positive, got {self.shots}")
        if self.budget_usd < 0:
            raise ValueError(f"a budget is non-negative, got {self.budget_usd}")

    @property
    def circuits(self) -> int:
        """One task and the readout calibration chapter 19 argues for."""
        return 1 + 1 + self.qubits

    def price(self) -> float:
        per_task, per_shot = PRICES[self.provider]
        return per_task * self.circuits + per_shot * self.circuits * self.shots


@dataclass(frozen=True)
class Question:
    text: str
    answer: bool


@dataclass(frozen=True)
class Verdict:
    problem: str
    decision: str
    reason: str
    questions: Tuple[Question, ...]
    usd: float

    @property
    def failed(self) -> str:
        """The first question that answered no, or 'none' when every one passed."""
        for question in self.questions:
            if not question.answer:
                return question.text
        return "none"

    def report(self) -> str:
        return f"{self.problem:20s}{self.decision:10s}{self.usd:9.2f}   {self.reason}"


def decide(problem: Problem) -> Verdict:
    """Ask the four questions in order and return the first decision they force."""
    usd = problem.price()
    questions = (
        Question(
            "Does the problem need a machine?",
            not (problem.purpose == "advantage" and problem.classical == "easy"),
        ),
        Question(
            "Does the circuit fit the machine?",
            problem.qubits <= MAX_QUBITS and problem.depth <= MAX_DEPTH,
        ),
        Question("Can the answer be checked?", problem.checkable),
        Question("Does the price fit the budget?", usd <= problem.budget_usd),
    )
    if not questions[0].answer:
        return Verdict(problem.name, "skip", "a classical program answers it in seconds", questions, usd)
    if not questions[1].answer:
        return Verdict(
            problem.name,
            "wait",
            f"{problem.qubits} qubits at depth {problem.depth} do not fit the 2026 machine",
            questions,
            usd,
        )
    if not questions[2].answer:
        return Verdict(problem.name, "simulate", "no ideal means a result cannot be told from a bug", questions, usd)
    if not questions[3].answer:
        return Verdict(problem.name, "refuse", f"{usd:.2f} USD is over the {problem.budget_usd:.2f} budget", questions, usd)
    return Verdict(problem.name, "device", "it fits, it is checkable, and it is affordable", questions, usd)


def cases() -> List[Problem]:
    """Six problems the book met, five decisions, and the numbers that force each one."""
    return [
        Problem("bv-4-demo", qubits=4, depth=10, classical="easy", checkable=True,
                purpose="learn", provider="ibm", shots=2048),
        Problem("bv-4-advantage", qubits=4, depth=10, classical="easy", checkable=True,
                purpose="advantage", provider="ibm", shots=2048),
        Problem("shor-2048", qubits=4096, depth=10**9, classical="hard", checkable=True,
                purpose="advantage", provider="ibm", shots=1),
        Problem("random-20", qubits=20, depth=40, classical="hard", checkable=False,
                purpose="learn", provider="ibm", shots=4096),
        Problem("ionq-demo", qubits=4, depth=10, classical="easy", checkable=True,
                purpose="learn", provider="ionq", shots=2048),
        Problem("maxcut-8", qubits=8, depth=30, classical="easy", checkable=True,
                purpose="advantage", provider="ibm", shots=4096),
    ]
