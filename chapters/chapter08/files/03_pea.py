"""Demo 03: phase estimation, exact and inexact.

Run: python3 chapters/chapter08/files/03_pea.py
"""

import phase

print("exact phases come back with certainty:")
for phi, n in ((0.125, 3), (0.25, 3), (0.375, 3), (0.5, 3), (0.0625, 4)):
    k, probability = phase.estimate(phi, n)
    print(f"  phi={phi:<8.4f} n={n}  k={k}  estimate={phase.phase_of(k, n):.4f}  P={probability:.4f}")

print()
print("a phase that does not fit in n bits comes back as the nearest one:")
for phi, n in ((1 / 3, 4), (0.2, 5), (0.7, 4)):
    k, probability = phase.estimate(phi, n)
    values = phase.distribution(phi, n)
    top = sorted(values.items(), key=lambda item: -item[1])[:3]
    print(f"  phi={phi:.4f} n={n}: k={k} -> {phase.phase_of(k, n):.4f} with P={probability:.4f}")
    for other, p in top:
        print(f"      k={other:2d} -> {phase.phase_of(other, n):.4f}  P={p:.4f}")

print()
print("the second and third candidates are neighbours of the answer, not random")
