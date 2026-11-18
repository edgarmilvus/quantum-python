"""Demo 04: six problems, four questions, five decisions.

Run: python3 chapters/chapter20/files/04_decide.py

Each case is a problem the book met, with the numbers that decide it. The table prints the
decision and the reason, and the second table prints the question that answered no, which
is the one a reader has to argue with.
"""

from ledger import cases, decide_problem

problems = cases()
verdicts = [decide_problem(problem) for problem in problems]

print(f"{'problem':20s}{'decision':>10s}{'USD':>9s}   reason")
for verdict in verdicts:
    print(verdict.report())
print()
print("the question that decided each one:")
for verdict in verdicts:
    print(f"  {verdict.problem:20s}{verdict.decision:9s}  {verdict.failed}")
print()
print("two of the six are refused by the same answer: a classical program already")
print("returns the number, so the only honest reason to run them is to learn, and")
print("that is a different purpose with a different budget.")
