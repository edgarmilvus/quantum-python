"""Demo 01: an oracle is a permutation, not a function.

Run: python3 chapters/chapter06/files/01_oracle.py
"""

import numpy as np

from oracle import bits, index, permutation

n = 2
f = lambda x: 1 if x in (1, 2) else 0

matrix = permutation(f, n)
print(f"truth table for n={n}: {[f(x) for x in range(1 << n)]}")
print(f"matrix shape: {matrix.shape}")
print(f"is a permutation: {np.allclose(matrix.sum(axis=0), 1.0) and np.allclose(matrix.sum(axis=1), 1.0)}")
print()
print(f"{'input':8s}{'output index':>14s}{'label':>10s}")
for x in range(1 << n):
    for y in (0, 1):
        column = index(x, y)
        row = int(np.argmax(matrix[:, column]))
        out_x, out_y = row >> 1, row & 1
        print(f"{format(x, f'0{n}b')}|{y}  {row:14d}  {format(out_x, f'0{n}b')}|{out_y}")

print()
print("the oracle changes only the last bit, and only when f says so")
