"""Exercise 5, file 3 of 3: the wiring.

The memo is the three files joined: `spend_book()` and six decisions in, one page out. The
wiring knows where the ledger lives; the other two files do not.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

from ledger import Spend, cases, decide_problem, spend_book

from memo_core import summarise, verdict_of
from memo_render import render


def memo(title: str = "Quantum Python") -> str:
    verdicts = [decide_problem(problem) for problem in cases()]
    summary = summarise(spend_book(), verdicts, title)
    return render(summary, verdict_of(summary))


def checks(check: Callable[[bool, str], None]) -> None:
    text = memo()
    check(text.startswith("Quantum Python"), "the memo is titled")
    check("0.00 USD" in text, "it says what was paid")
    check("984.84 USD" in text, "and what was refused")
    check("2,503" not in text and "2503" in text, "the assertion count is a number, not a formatted string")
    check("1 device" in text, "the decisions are tallied")

    summary = summarise(spend_book(), [decide_problem(problem) for problem in cases()])
    check(summary["chapters"] == 19, "nineteen chapters")
    check(summary["runs"] == 40, "forty runs")
    check(summary["proofs"] == 2503, "2,503 assertions")
    check("19 chapters, 40 runs, 2503 assertions" in summary["headline"], "the headline names all three")
    check(verdict_of(summary).startswith("the book spent nothing"), "the sentence says the book spent nothing")
    check(sum(summary["decisions"].values()) == 6, "the tally covers six cases")

    check(memo() == text, "the memo is deterministic")
    check("nan" not in text.lower(), "no number failed to compute")
    check(text.endswith("\n"), "the page ends on a newline")

    for title in ("", "   "):
        try:
            summarise(spend_book(), [], title)
        except ValueError:
            check(True, f"a title of {title!r} is refused")
        else:
            check(False, f"a title of {title!r} is refused")

    empty = Spend(
        chapters=0, runs=0, live=0, local=0, shots=0, live_shots=0,
        proofs=0, artifacts=0, words=0, usd=0.0, refused=0.0,
    )
    try:
        summarise(empty, [])
    except ValueError:
        check(True, "a spend with no chapter is refused")
    else:
        check(False, "a spend with no chapter is refused")

    try:
        render(summary, "")
    except ValueError:
        check(True, "a memo with no sentence is refused")
    else:
        check(False, "a memo with no sentence is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
