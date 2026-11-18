"""Chapter 20 harness: the book's contracts, runs, bill and decisions.

Run: python3 chapters/chapter20/files/run_ex20.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ledger import (
    BOOK_CHAPTERS,
    BOOK_RUNS,
    MAX_DEPTH,
    MAX_QUBITS,
    Problem,
    chapter_table,
    chapters,
    counts,
    decide_problem,
    decision_table,
    free,
    provider_table,
    refused_quote,
    runs,
    spend_book,
    summary,
)

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


# -- the contracts ------------------------------------------------------
section("the contracts")
found = chapters()
check(len(found) == BOOK_CHAPTERS == 19, "nineteen contracts")
check(found[0].number == 1, "the first is chapter 1")
check(found[-1].number == 19 and found[-1].title == "The Pipeline", "the last is the pipeline")
check(all(chapter.exercises == 5 for chapter in found), "every chapter has five exercises")
check(all(chapter.floor == 14000 for chapter in found), "every floor is 14,000")
check(all(chapter.proofs > 0 for chapter in found), "every chapter has assertions")
check(sum(chapter.proofs for chapter in found) == 2503, "2,503 assertions in total")
check(sum(chapter.artifacts for chapter in found) == 357, "357 published files")
check([chapter.number for chapter in found if chapter.from_record] == [2], "chapter 2 resolves from its record")
check(len({chapter.title for chapter in found}) == 19, "the titles are distinct")
check(found[5].proofs == 206, "chapter 6 carries the most assertions")
check(found[16].proofs == 98, "chapter 17 carries the fewest")

# -- the runs -----------------------------------------------------------
section("the runs")
recorded = runs()
check(len(recorded) == BOOK_RUNS == 40, "forty runs")
check(sum(run.live for run in recorded) == 21, "twenty-one live")
check(sum(not run.live for run in recorded) == 19, "nineteen local")
check(sum(run.shots for run in recorded) == 588176, "588,176 shots")
check(len({run.number for run in recorded}) == 40, "the numbers are unique")
check(recorded[-1].number == 40, "the last is 0040")
by_number = {run.number: run for run in recorded}
check(by_number[39].shots == 12288, "2048 x 6 is twelve thousand")
check(by_number[8].shots == 200000, "200k is two hundred thousand")
check(by_number[20].shots == 0, "a saved snapshot has no shots")
check(by_number[1].provider == "IBM Quantum", "the first live run is IBM")
check(by_number[25].provider.startswith("qBraid"), "0025 is the qBraid aggregator")
check(len({run.provider for run in recorded}) >= 8, "at least eight provider strings")
check(all(not run.live for run in recorded if run.provider.startswith("local")), "local rows are local")

# -- the bill -----------------------------------------------------------
section("the bill")
total = spend_book()
check(total.usd == 0.0, "the book paid nothing")
check(total.chapters == 19 and total.runs == 40, "nineteen chapters, forty runs")
check(total.live + total.local == total.runs, "live and local partition the runs")
check(total.proofs == 2503, "the bill carries the assertions")
check(total.words == 299122, "299,122 words in chapters 1-19")
check(total.artifacts == 357, "357 artifacts")
check(abs(refused_quote() - 984.84) < 1e-9, "the refused invoice is 984.84")
check(free("local") and free("IBM Quantum") and free("qBraid (aggregator)"), "the free tiers are recognised")
check(not free("Rigetti"), "a paid provider is not")

paid = recorded[0].__class__(99, "fake", "Rigetti", "Ankaa", 100, "a paid run")
try:
    spend_book(records=(paid,))
except ValueError as error:
    check("Rigetti" in str(error), "a paid run is refused by name")
else:
    check(False, "a paid run is refused by name")

small = spend_book(records=recorded[:2])
check(small.runs == 2 and small.chapters == 19, "a subset of runs keeps the chapters")
check(small.shots == 2048, "two runs at 1,024 shots are 2,048")

# -- the decisions ------------------------------------------------------
section("the decisions")
problems = None
from ledger import cases  # noqa: E402

problems = cases()
check(len(problems) == 6, "six cases")
verdicts = [decide_problem(problem) for problem in problems]
check([verdict.decision for verdict in verdicts] == ["device", "skip", "wait", "simulate", "refuse", "skip"],
      "and five distinct decisions")
check(counts(verdicts) == (("device", 1), ("skip", 2), ("wait", 1), ("simulate", 1), ("refuse", 1)),
      "the tally is 1-2-1-1-1")

back = {verdict.problem: verdict for verdict in verdicts}
check(back["bv-4-demo"].failed == "none", "the demo passes every question")
check(back["bv-4-advantage"].failed == "Does the problem need a machine?", "the advantage case fails the first")
check(back["shor-2048"].failed == "Does the circuit fit the machine?", "Shor fails the second")
check(back["random-20"].failed == "Can the answer be checked?", "the random circuit fails the third")
check(back["ionq-demo"].failed == "Does the price fit the budget?", "IonQ fails the fourth")
check(abs(back["ionq-demo"].usd - 984.84) < 1e-9, "at 984.84")
check(problems[0].circuits == 6, "a four-qubit problem is six circuits")
check(MAX_QUBITS == 156 and MAX_DEPTH == 100, "the machine is 156 qubits and depth 100")

try:
    Problem("shor", qubits=0, depth=10, classical="hard", checkable=True, purpose="advantage")
except ValueError:
    check(True, "zero qubits is refused")
else:
    check(False, "zero qubits is refused")

for bad in (
    dict(name="x", qubits=4, depth=0, classical="hard", checkable=True, purpose="learn"),
    dict(name="x", qubits=4, depth=10, classical="maybe", checkable=True, purpose="learn"),
    dict(name="x", qubits=4, depth=10, classical="hard", checkable=True, purpose="fun"),
    dict(name="x", qubits=4, depth=10, classical="hard", checkable=True, purpose="learn", provider="nope"),
    dict(name="x", qubits=4, depth=10, classical="hard", checkable=True, purpose="learn", shots=0),
    dict(name="x", qubits=4, depth=10, classical="hard", checkable=True, purpose="learn", budget_usd=-1),
):
    try:
        Problem(**bad)
    except ValueError:
        check(True, f"{bad} is refused")
    else:
        check(False, f"{bad} is refused")

# -- the report ---------------------------------------------------------
section("the report")
table = chapter_table(found)
check(table.count("\n") == 19, "the chapter table has a header and nineteen rows")
check("The Pipeline" in table, "and names the last chapter")
providers = provider_table(recorded)
check(providers.count("\n") == 10, "ten provider strings in the table")
check("IBM Quantum" in providers, "including Big Blue")
decisions = decision_table(verdicts)
check(decisions.count("\n") == 6, "the decision table is six rows plus a header")
page = summary(total, verdicts)
check("0.00 USD" in page, "the page says what was paid")
check("984.84 USD" in page, "and what was refused")
check("1 device, 2 skip, 1 wait, 1 simulate, 1 refuse" in page, "and how the cases landed")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
