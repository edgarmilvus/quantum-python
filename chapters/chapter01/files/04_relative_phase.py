"""Demo 04: a relative phase changes everything you can measure.

Run: python3 chapters/chapter01/files/04_relative_phase.py
"""

from sampling import sample_counts
from state import StateVector, hadamard, z_gate

zero = StateVector.zero()

# H then H is the identity: the second H undoes the first.
identity_like = hadamard(hadamard(zero))
# H then Z then H is X: the phase flip survives the interference.
flipped = hadamard(z_gate(hadamard(zero)))

print(f"H H   -> {identity_like}  p={identity_like.probabilities()}")
print(f"H Z H -> {flipped}  p={flipped.probabilities()}")
print()
print(f"H H   counts: {sample_counts(identity_like, shots=1000, seed=11)}")
print(f"H Z H counts: {sample_counts(flipped, shots=1000, seed=11)}")
print()
print("same input state, same gate count, opposite result")
