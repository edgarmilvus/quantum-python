"""Demo 05: the one page a reader takes to work on Monday.

Run: python3 chapters/chapter20/files/05_report.py

The summary is the book measured against itself, and the decision table is the procedure.
Neither replaces the nineteen chapters: the page is what remains after them, which is the
only kind of summary a technical book is allowed to end on.
"""

from ledger import cases, counts, decide_problem, decision_table, spend_book, summary

verdicts = [decide_problem(problem) for problem in cases()]
print(summary(spend_book(), verdicts))
print()
print(decision_table(verdicts))
print()
tally = ", ".join(f"{count} {name}" for name, count in counts(verdicts))
print(f"the six cases land on {tally}.")
print()
print("run the pipeline when the decision is device; run nothing when it is skip;")
print("write the paper when it is wait; and when it is simulate, the answer is a")
print("simulator and a sentence about what the device would have to become.")
