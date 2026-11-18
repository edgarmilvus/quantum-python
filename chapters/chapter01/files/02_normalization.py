"""Demo 02: what happens when the numbers do not add up to one.

Run: python3 chapters/chapter01/files/02_normalization.py
"""

from state import StateError, UnnormalizedState, StateVector

raw = [1.0, 0.1]

try:
    StateVector.from_amplitudes(raw)
except UnnormalizedState as exc:
    print(f"refused: {exc}")

repaired = StateVector(raw).normalized()
print(f"repaired amplitudes: {repaired.amplitudes}")
print(f"repaired norm:       {repaired.norm:.12f}")

try:
    StateVector([0.0, 0.0]).normalized()
except StateError as exc:
    print(f"refused again: {exc}")
