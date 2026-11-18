"""Demo 01: the Bell pair, four amplitudes, and what a measurement predicts.

Run: python3 chapters/chapter04/files/01_bell.py
"""

import numpy as np

import bell

state = bell.bell_state()
print(f"amplitudes: {np.round(state, 4)}")
print(f"probabilities: {np.round(np.abs(state) ** 2, 4)}")
print(f"norm: {np.sum(np.abs(state) ** 2):.12f}")
print()

print(f"{'setting':16s}{'angles':>14s}{'E':>10s}{'cos(a-b)':>10s}")
for name, (angle_a, angle_b) in bell.SETTINGS.items():
    expected = bell.expectation_from_probabilities(bell.probabilities(angle_a, angle_b))
    print(f"{name:16s}{f'{angle_a:g} / {angle_b:g}':>14s}{expected:10.4f}"
          f"{bell.predicted_expectation(angle_a, angle_b):10.4f}")

print()
simulated = bell.simulate()
print(f"S on an ideal pair: {bell.chsh(simulated):.6f}")
print(f"classical bound:    {bell.CLASSICAL_BOUND:.6f}")
print(f"Tsirelson bound:    {bell.TSIRELSON_BOUND:.6f}")
