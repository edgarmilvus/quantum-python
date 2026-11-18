"""Demo 03: a shot budget, and the cost of testing four things at once.

Run: python3 chapters/chapter05/files/03_budget.py
"""

from stats import bonferroni, shots_for

print(f"{'half-width':>12s}{'shots at p=0.5':>16s}{'shots at p=0.9':>16s}")
for precision in (0.1, 0.05, 0.02, 0.01, 0.005):
    print(f"{precision:12.3f}{shots_for(precision):16d}{shots_for(precision, p=0.9):16d}")

print()
print(f"{'tests':>6s}{'alpha per test at family 0.05':>32s}")
for tests in (1, 4, 16, 100):
    print(f"{tests:6d}{bonferroni(0.05, tests):32.5f}")

print()
print("four settings at a 5% family error need a 1.25% threshold each")
print("a result that clears 5% once, among sixteen, does not clear the family")
