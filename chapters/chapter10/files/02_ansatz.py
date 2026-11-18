"""Demo 02: one knob, and the energy it produces.

Run: python3 chapters/chapter10/files/02_ansatz.py
"""

import numpy as np

import h2

print("the ansatz: X on qubit 0, Ry(theta) on qubit 1, CNOT from 1 to 0")
print()
print(f"{'theta':>8s}{'state (01,10 amplitudes)':>28s}{'energy':>12s}")
for theta in (0.0, -0.1, -0.2235, -0.4, np.pi / 2, np.pi):
    state = h2.ansatz_state(theta)
    amplitudes = f"{state[1].real:+.4f}, {state[2].real:+.4f}"
    print(f"{theta:8.4f}{amplitudes:>28s}{h2.energy(theta):12.6f}")

print()
angle, value = h2.best_angle()
print(f"the minimum on a grid of 200,000 angles: theta = {angle:.6f}, E = {value:.6f}")
analytic_angle, analytic_value, _ = h2.analytic_minimum()
print(f"the exact minimum by projection:         theta = {analytic_angle:.6f}, E = {analytic_value:.6f}")
print()
print(f"Hartree-Fock at theta = 0: {h2.energy(0.0):.6f}")
print(f"the knob moves the energy by {(value - h2.energy(0.0)) * 1000:.2f} mHa")
