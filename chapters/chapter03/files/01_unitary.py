"""Demo 01: the same two gates, two orders, two different unitaries.

Run: python3 chapters/chapter03/files/01_unitary.py
"""

import numpy as np

from circuit import Circuit

bell = Circuit(2).add("h", 0).add("cx", 0, 1)
other = Circuit(2).add("cx", 0, 1).add("h", 0)

print("H then CX:")
print(np.round(bell.unitary(), 3))
print()
print("CX then H:")
print(np.round(other.unitary(), 3))
print()
print(f"is unitary: {bell.is_unitary()}")
print(f"same unitary: {np.allclose(bell.unitary(), other.unitary())}")
print(f"distance: {np.max(np.abs(bell.unitary() - other.unitary())):.3f}")
print()
print(f"ops: {bell.gate_count()}, depth: {bell.depth()}")
print(f"ops: {other.gate_count()}, depth: {other.depth()}")
