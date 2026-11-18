"""Demo 03: the exact optimum, and where the textbook approximation fails.

Run: python3 chapters/chapter07/files/03_optimal.py
"""

import grover

print(f"{'N':>8s}{'k exact':>9s}{'P exact':>9s}{'k approx':>10s}{'P approx':>10s}")
for n in (2, 3, 4, 5, 6, 8):
    size = 1 << n
    exact = grover.optimal_iterations(size)
    approx = grover.approx_iterations(size)
    print(f"{size:8d}{exact:9d}{grover.success_probability(0, n, exact):9.4f}"
          f"{approx:10d}{grover.success_probability(0, n, approx):10.4f}")

print()
print("at N=4 the approximation asks for two iterations where one is optimal:")
print(f"  k=1 gives {grover.success_probability(0, 2, 1):.4f}")
print(f"  k=2 gives {grover.success_probability(0, 2, 2):.4f}")
print()
print("pi/4 * sqrt(N) is the asymptotic optimum; the exact one is round(pi/(4 theta) - 1/2)")
