"""Demo 02: Wilson against the textbook interval, at the edges.

Run: python3 chapters/chapter05/files/02_intervals.py
"""

import math

from stats import wilson


def normal_interval(count: int, shots: int, z: float = 1.96):
    p = count / shots
    half = z * math.sqrt(p * (1 - p) / shots)
    return p - half, p + half


print(f"{'count/shots':>14s}{'normal':>22s}{'wilson':>22s}")
for count, shots in ((0, 20), (1, 20), (2, 20), (10, 20), (19, 20), (20, 20), (0, 1000), (1000, 1000)):
    n = normal_interval(count, shots)
    w = wilson(count, shots)
    print(f"{f'{count}/{shots}':>14s}{f'[{n[0]:+.4f}, {n[1]:+.4f}]':>22s}"
          f"{f'[{w[0]:.4f}, {w[1]:.4f}]':>22s}")

print()
print("the normal interval leaves [0, 1] as soon as k is 0 or k = n; Wilson does not")
