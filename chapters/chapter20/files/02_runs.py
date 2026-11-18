"""Demo 02: forty runs, grouped by the provider that answered.

Run: python3 chapters/chapter20/files/02_runs.py

The index is the only record every run has: one row with a number, a case, a provider, a
backend, a shot count and a sentence. The provider table groups the rows, and the shot
total is the book's sample size, not its effort.
"""

from ledger import provider_table, runs

found = runs()
print(provider_table(found))
print()
print(f"{len(found)} runs, {sum(r.live for r in found)} live, {sum(not r.live for r in found)} local")
print(f"shots: {sum(r.shots for r in found)}, of which {sum(r.shots for r in found if r.live)} were on a provider")
print(f"largest: {max(found, key=lambda run: run.shots).report()}")
print(f"first live: {next(run for run in found if run.live).report()}")
print()
print("the local rows are not failures. They are the runs whose answer a reader can")
print("recompute without an account, and they are the majority of the book on purpose.")
