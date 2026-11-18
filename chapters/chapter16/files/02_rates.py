"""Demo 02: the binomial tail, and the rate the code delivers.

Run: python3 chapters/chapter16/files/02_rates.py

The logical error is the probability that more than half the qubits flip, which is
a binomial tail and needs no simulation. The Monte Carlo agrees with it to three
decimals, and the table shows why a distance is worth its qubits at 5% and barely
worth them at 30%.
"""

import numpy as np

from ecc import code, sim

print(f"{'p':>6s}{'d=3':>10s}{'d=5':>10s}{'d=7':>10s}{'d=3 / p':>10s}")
for p in (0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40):
    values = [code.logical_error_ideal(d, p) for d in (3, 5, 7)]
    print(f"{p:6.2f}{values[0]:10.5f}{values[1]:10.5f}{values[2]:10.5f}{values[0] / p:10.4f}")
print()

wrong, trials = sim.sample_bitflips(3, 0.10, 20000, seed=1)
print(f"Monte Carlo, d=3, p=0.10: {wrong}/{trials} = {wrong / trials:.5f}")
print(f"binomial:                                  {code.logical_error_ideal(3, 0.10):.5f}")
print()

print("the break-even point of a single-axis code:")
for d in (3, 5, 7):
    print(f"  d={d}: {sim.break_even(d):.4f}")
print()
print("half the qubits flipping is the point where a majority is a coin flip, so the")
print("code has no threshold below it; a surface code does, because it checks both axes.")
