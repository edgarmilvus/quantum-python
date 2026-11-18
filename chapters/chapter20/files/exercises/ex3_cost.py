"""Exercise 3 (measure): what one proof cost, in the three currencies the book has.

Run: python3 chapters/chapter20/files/exercises/ex3_cost.py

The bill is zero dollars, and a zero divided by anything is still zero, so the exercise
measures the other two currencies: words per proof and shots per live run. The third is
the counterfactual — the refused invoice divided by the assertions it would have bought —
which is the only number in the chapter that is not zero.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

from ledger import refused_quote, spend_book


def per(total: float, unit: int) -> float:
    if unit <= 0:
        raise ValueError(f"a unit count is positive, got {unit}")
    if total < 0:
        raise ValueError(f"a total is non-negative, got {total}")
    return total / unit


def measures() -> dict:
    total = spend_book()
    return {
        "words_per_chapter": per(total.words, total.chapters),
        "proofs_per_chapter": per(total.proofs, total.chapters),
        "words_per_proof": per(total.words, total.proofs),
        "shots_per_live_run": per(total.live_shots, total.live),
        "usd_per_proof": per(total.usd, total.proofs),
        "refused_per_proof": per(refused_quote(), total.proofs),
    }


def checks(check: Callable[[bool, str], None]) -> None:
    total = spend_book()
    measured = measures()

    check(total.proofs == 2503, "2,503 assertions")
    check(total.words == 299122, "299,122 words")
    check(total.usd == 0.0, "and nothing paid")

    check(abs(measured["words_per_chapter"] - 15743.3) < 0.2, "15,743 words per chapter")
    check(abs(measured["proofs_per_chapter"] - 131.7) < 0.2, "132 assertions per chapter")
    check(abs(measured["words_per_proof"] - 119.5) < 0.2, "120 words per assertion")
    check(abs(measured["shots_per_live_run"] - 16702.5) < 0.5, "16,702 shots per live run")
    check(measured["usd_per_proof"] == 0.0, "zero dollars per assertion")
    check(abs(measured["refused_per_proof"] - 0.3935) < 0.001, "the refused invoice is 0.39 per assertion")

    check(measured["words_per_proof"] < measured["words_per_chapter"], "a proof is cheaper than a chapter")
    check(measured["shots_per_live_run"] > 10000, "a live run carries more than ten thousand shots")

    for bad in (0, -1):
        try:
            per(10.0, bad)
        except ValueError:
            check(True, f"{bad} units is refused")
        else:
            check(False, f"{bad} units is refused")

    try:
        per(-1.0, 10)
    except ValueError:
        check(True, "a negative total is refused")
    else:
        check(False, "a negative total is refused")

    check(abs((total.usd + refused_quote()) - 984.84) < 1e-9, "paid plus refused is the invoice")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
