"""Demo 03: a global phase changes nothing you can measure.

Run: python3 chapters/chapter01/files/03_global_phase.py
"""

from sampling import sample_counts
from state import StateVector, hadamard

state = hadamard(StateVector.zero())
rotated = state.with_phase(1j)

print(f"before: {state}")
print(f"after:  {rotated}")
print(f"p before: {state.probabilities()}")
print(f"p after:  {rotated.probabilities()}")
print()
print(f"counts before: {sample_counts(state, shots=1000, seed=7)}")
print(f"counts after:  {sample_counts(rotated, shots=1000, seed=7)}")
print()
print(f"inner product <before|after> = {state.inner(rotated)}")
print("the vector changed, the distribution did not")
