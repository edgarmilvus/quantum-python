"""Demo 03: phase on one wire is invisible until the wires interfere.

Run: python3 chapters/chapter02/files/03_phase.py
"""

import numpy as np

from gates import H, S, T
from register import Register

print("H on wire 0, then S on wire 0, then H on wire 0")
a = Register.zero().apply(H, 0)
print(f"  after H:    {np.round(a.amplitudes, 4)}  p={np.round(a.probabilities(), 4)}")
b = a.apply(S, 0)
print(f"  after S:    {np.round(b.amplitudes, 4)}  p={np.round(b.probabilities(), 4)}")
c = b.apply(H, 0)
print(f"  after H:    {np.round(c.amplitudes, 4)}  p={np.round(c.probabilities(), 4)}")
print()

print("the same with T, which is a pi/4 phase instead of pi/2")
d = Register.zero().apply(H, 0).apply(T, 0).apply(H, 0)
print(f"  final:      {np.round(d.amplitudes, 4)}  p={np.round(d.probabilities(), 4)}")
print()

print("and with S on wire 1 instead of wire 0")
e = Register.zero().apply(H, 0).apply(S, 1).apply(H, 0)
print(f"  final:      {np.round(e.amplitudes, 4)}  p={np.round(e.probabilities(), 4)}")
print()
print("counts at 1000 shots, seed 5:")
for name, state in (("no phase", Register.zero().apply(H, 0).apply(H, 0)), ("S on wire 0", c), ("S on wire 1", e)):
    print(f"  {name:12s} {state.sample(1000, seed=5)}")
