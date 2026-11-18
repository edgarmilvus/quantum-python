"""What the book cost, and what it refused to cost.

The ledger's second half is arithmetic on the records: nineteen contracts, forty runs,
the assertions they carry, and the one invoice the pipeline declined. The money is zero
because every provider the book used gave its tier away, and the module says so by
refusing a provider it does not recognise as free rather than by printing a zero.

The other number is the one a reader should keep: 984.84 dollars is what the same job
would have cost on a provider that charges per shot, and chapter 19's estimate said no.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from . import spec

# The providers this book actually used, all on a free tier. A prefix, not an equality,
# because the index records the saved snapshots and the mixed runs as prose.
FREE = ("local", "IBM Quantum", "Quantum Inspire", "IonQ", "qBraid")

# Chapter 19's refused job: six circuits, 2,048 shots, IonQ's two-part tariff.
REFUSED_CIRCUITS = 6
REFUSED_SHOTS = 2048
IONQ_PER_TASK = 0.30
IONQ_PER_SHOT = 0.08


@dataclass(frozen=True)
class Spend:
    chapters: int
    runs: int
    live: int
    local: int
    shots: int
    live_shots: int
    proofs: int
    artifacts: int
    words: int
    usd: float
    refused: float

    def report(self) -> str:
        return (
            f"chapters   {self.chapters}\n"
            f"runs       {self.runs} ({self.live} live, {self.local} local)\n"
            f"shots      {self.shots} ({self.live_shots} on a provider)\n"
            f"proofs     {self.proofs}\n"
            f"artifacts  {self.artifacts}\n"
            f"words      {self.words}\n"
            f"paid       {self.usd:.2f} USD\n"
            f"refused    {self.refused:.2f} USD"
        )


def free(provider: str) -> bool:
    """Whether a recorded provider is one of the free tiers the book used."""
    return any(provider.startswith(name) for name in FREE)


def refused_quote() -> float:
    """The IonQ invoice chapter 19's estimate refused, recomputed rather than quoted."""
    return IONQ_PER_TASK * REFUSED_CIRCUITS + IONQ_PER_SHOT * REFUSED_CIRCUITS * REFUSED_SHOTS


def spend(
    through_chapters: int = spec.BOOK_CHAPTERS,
    through_runs: int = spec.BOOK_RUNS,
    records: Optional[Sequence[spec.Run]] = None,
) -> Spend:
    """The book's bill, or a refusal if a run names a provider that is not free.

    `records` exists for the harness: a paid run can be fed in without editing the
    index, and the refusal is then testable.
    """
    chapters: Tuple[spec.Chapter, ...] = spec.chapters(through_chapters)
    runs: Tuple[spec.Run, ...] = tuple(records) if records is not None else spec.runs(through_runs)
    for run in runs:
        if not free(run.provider):
            raise ValueError(
                f"run {run.number:04d} used {run.provider!r}, which is not a free tier; "
                "the ledger does not report zero for a provider it cannot price"
            )
    words = sum(spec.words(f"chapter{chapter.number:02d}") for chapter in chapters)
    return Spend(
        chapters=len(chapters),
        runs=len(runs),
        live=sum(run.live for run in runs),
        local=sum(not run.live for run in runs),
        shots=sum(run.shots for run in runs),
        live_shots=sum(run.shots for run in runs if run.live),
        proofs=sum(chapter.proofs for chapter in chapters),
        artifacts=sum(chapter.artifacts for chapter in chapters),
        words=words,
        usd=0.0,
        refused=refused_quote(),
    )
