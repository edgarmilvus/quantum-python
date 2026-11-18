"""Exercise 5, file 1 of 3: the pure part of the Monday memo.

A spend and a list of verdicts in, one dictionary out. No file, no printing, no clock.
"""

from __future__ import annotations

from typing import Dict, Sequence

from ledger import Spend, Verdict, counts


def summarise(total: Spend, verdicts: Sequence[Verdict], title: str = "Quantum Python") -> Dict:
    if not title or not title.strip():
        raise ValueError("a memo needs a title")
    if total.chapters <= 0:
        raise ValueError(f"a memo needs a chapter, got {total.chapters}")
    if total.proofs <= 0:
        raise ValueError(f"a memo needs an assertion, got {total.proofs}")
    return {
        "title": title,
        "chapters": total.chapters,
        "runs": total.runs,
        "live": total.live,
        "proofs": total.proofs,
        "words": total.words,
        "usd": total.usd,
        "refused": total.refused,
        "decisions": dict(counts(verdicts)),
        "headline": (
            f"{total.chapters} chapters, {total.runs} runs, {total.proofs} assertions, "
            f"{total.usd:.2f} USD paid, {total.refused:.2f} USD refused"
        ),
    }


def verdict_of(memo: Dict) -> str:
    """One sentence, because a memo with a table and no sentence is a spreadsheet."""
    if memo["usd"] > 0.0:
        return "the book spent money, and the ledger knows on what"
    if memo["refused"] > 0.0:
        return "the book spent nothing and declined a job that would have cost more than the book"
    return "the book spent nothing and refused nothing, which would mean it never priced a task"
