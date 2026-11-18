"""Demo 05: five representations of one prepared state, and what reconciles them.

Run: python3 chapters/chapter02/files/05_ordering.py
"""

import numpy as np

from ordering import (
    bell_cirq,
    bell_numpy,
    bell_qiskit,
    comparison,
    little_to_big,
    reconciliation,
)

print(f"{'implementation':22s}{'index of the 1':>16s}   vector")
for name, array, index in comparison():
    print(f"{name:22s}{index:16d}   {np.round(array, 3)}")

print()
print("distance from our convention:")
for name, value in reconciliation().items():
    print(f"  {name:16s} {value:.3e}")

print()
print("a symmetric state hides the defect:")
for name, array in (("numpy", bell_numpy()), ("qiskit", bell_qiskit()), ("cirq", bell_cirq())):
    print(f"  {name:8s} {np.round(array, 4)}  distance "
          f"{np.max(np.abs(array - bell_numpy())):.3e}")

print()
print("after converting Qiskit's order:")
print(f"  {np.round(little_to_big(np.array([0, 1, 0, 0])), 3)}")
