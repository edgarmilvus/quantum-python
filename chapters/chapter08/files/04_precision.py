"""Demo 04: how many bits buy how much confidence.

Run: python3 chapters/chapter08/files/04_precision.py
"""

import math

import phase

print(f"{'n':>2s}{'bits':>6s}{'precision':>12s}{'worst P':>10s}{'best P':>9s}")
for n in (2, 3, 4, 5, 6, 8):
    worst = min(phase.success_probability(phi / 1000, n) for phi in range(1, 1000))
    best = max(phase.success_probability(phi / 1000, n) for phi in range(1, 1000))
    print(f"{n:2d}{n:6d}{phase.precision(n):12.5f}{worst:10.4f}{best:9.4f}")

print()
print(f"the textbook floor is 4/pi^2 = {4 / math.pi ** 2:.4f}")
print("the worst case is a phase exactly halfway between two representable values")
print()
half = 0.5 / (1 << 4)
k, probability = phase.estimate(half, 4)
print(f"at n=4, phi={half:.4f} (halfway): P={probability:.4f}")
print(f"at n=5, the same phase is representable: P={phase.success_probability(half, 5):.4f}")
