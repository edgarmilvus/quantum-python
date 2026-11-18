"""Demo 03: Deutsch-Jozsa, and what one query buys.

Run: python3 chapters/chapter06/files/03_dj.py
"""

from algorithms import classical_queries_deutsch_jozsa, deutsch_jozsa, deutsch_jozsa_answer
from oracle import balanced, constant

print(f"{'n':>2s}{'function':16s}{'answer':10s}{'P(answer)':>11s}{'classical':>11s}")
for n in (1, 2, 3, 4):
    for kind, f in (("constant 0", constant(0)), ("constant 1", constant(1)), ("balanced 1", balanced(1, n))):
        distribution = deutsch_jozsa(f, n)
        answer = deutsch_jozsa_answer(distribution)
        peak = max(distribution.values())
        classical = classical_queries_deutsch_jozsa(f, n)
        print(f"{n:2d}{kind:16s}{answer:10s}{peak:11.4f}{classical:11d}")

print()
print("one query decides it, and the answer comes back as a single outcome")
print("the classical program needs to look at half the table plus one")
print()
print("the number of outcomes the algorithm can return:")
for n in (1, 2, 3, 4):
    support = len([v for v in deutsch_jozsa(balanced(1, n), n).values() if v > 1e-12])
    print(f"  n={n}: {support} outcome(s) with non-zero probability")
