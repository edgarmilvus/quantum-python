"""Demo 01: two complex numbers, and the two probabilities they imply.

Run: python3 chapters/chapter01/files/01_amplitudes.py
"""

import numpy as np

from state import StateVector

state = StateVector([np.sqrt(0.75), np.sqrt(0.25) * 1j])

print(f"amplitudes: {state.amplitudes}")
print(f"norm:       {state.norm:.12f}")
print(f"p:          {state.probabilities()}")
print()
for label, amplitude, p in zip(state.labels(), state.amplitudes, state.probabilities()):
    print(f"  {label}: amplitude {amplitude:+.6f}, |a|^2 = {p:.6f}")
print()
print(f"P(0) + P(1) = {state.probabilities().sum():.12f}")
