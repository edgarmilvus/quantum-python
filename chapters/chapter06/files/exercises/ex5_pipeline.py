"""Exercise 5, file 3 of 3: the wiring.

Builds the two problems from a secret and prints both reports. The only file that
prints, and the only one that chooses which functions to ask about.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

from algorithms import bernstein_vazirani
from oracle import balanced, constant, linear
from pipeline_core import bernstein_vazirani_report, deutsch_jozsa_report, rows
from pipeline_render import render

N = 4


def deutsch_jozsa_text(kind: str = "balanced", secret: int = 5) -> str:
    f = constant(0) if kind == "constant" else balanced(secret, N)
    return render(rows(deutsch_jozsa_report(f, N)), f"Deutsch-Jozsa ({kind})")


def bernstein_vazirani_text(secret: int = 5) -> str:
    return render(rows(bernstein_vazirani_report(secret, N)), "Bernstein-Vazirani")


def checks(check: Callable[[bool, str], None]) -> None:
    balanced_report = deutsch_jozsa_report(balanced(5, N), N)
    check(balanced_report["answer"] == "balanced", "the balanced function is labelled balanced")
    check(abs(balanced_report["probability"] - 1.0) < 1e-12, "with a certain outcome")
    check(balanced_report["classical_queries"] == 2, "the classical program needed two queries")
    check(balanced_report["quantum_queries"] == 1, "the quantum one needed one")
    check(abs(balanced_report["ratio"] - 2.0) < 1e-12, "the ratio is two")

    constant_report = deutsch_jozsa_report(constant(1), N)
    check(constant_report["answer"] == "constant", "the constant function is labelled constant")
    check(constant_report["classical_queries"] == 9, "and cost nine classical queries")
    check(abs(constant_report["ratio"] - 9.0) < 1e-12, "so the ratio is nine")

    bv_report = bernstein_vazirani_report(5, N)
    check(bv_report["outcome"] == "0101", "the secret comes back")
    check(bv_report["classical_queries"] == 4, "four classical queries")
    check(abs(bv_report["ratio"] - 4.0) < 1e-12, "and a ratio of four")

    text = bernstein_vazirani_text()
    check("Bernstein-Vazirani" in text and "0101" in text, "the report names the secret")
    check(text.count("\n") >= 6, "a header and six rows")
    check(deutsch_jozsa_text() == deutsch_jozsa_text(), "the wiring is deterministic")

    check(len(berstein := bernstein_vazirani(5, N)) == 16, "the distribution has sixteen outcomes")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
