"""Demo 02: the same gate on wire 0 and on wire 1 lands in different slots.

Run: python3 chapters/chapter02/files/02_wire.py
"""

import numpy as np

from gates import X, embed
from register import Register

print("matrix for X on wire 0:")
print(embed(X, 0))
print()
print("matrix for X on wire 1:")
print(embed(X, 1))
print()

zero = Register.zero()
for wire in (0, 1):
    moved = zero.apply(X, wire)
    index = int(np.argmax(np.abs(moved.amplitudes)))
    print(f"X on wire {wire}: index {index}, label {moved.bitstring(index)}, "
          f"p={np.round(moved.probabilities(), 3)}")
