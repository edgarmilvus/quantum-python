"""Demo 01: a frequency, and the interval that makes it a claim.

Run: python3 chapters/chapter05/files/01_sampling.py
"""

import numpy as np

from stats import interval_width, standard_error, wilson

print(f"{'shots':>8s}{'count':>8s}{'frequency':>12s}{'1 sigma':>10s}{'95% interval':>22s}{'width':>9s}")
for shots, count in ((20, 10), (100, 50), (1000, 500), (10000, 5000), (100000, 50000)):
    p = count / shots
    low, high = wilson(count, shots)
    print(f"{shots:8d}{count:8d}{p:12.4f}{standard_error(p, shots):10.4f}"
          f"{f'[{low:.4f}, {high:.4f}]':>22s}{interval_width(count, shots):9.4f}")

print()
rng = np.random.default_rng(2)
true_p = 0.5
for shots in (20, 100, 1000, 10000):
    hits = 0
    for _ in range(2000):
        count = int(rng.binomial(shots, true_p))
        low, high = wilson(count, shots)
        hits += low <= true_p <= high
    print(f"{shots:6d} shots: the interval contained the truth {hits / 2000:.3f} of the time")

print()
print("a 95% interval covers the truth about 95% of the time, at every sample size")
