"""Demo 03: any one-qubit gate is three rotations.

Run: python3 chapters/chapter03/files/03_decompose.py
"""

import numpy as np

from circuit import H, S, T, X, gate_matrix
from decompose import distance_up_to_phase, rebuild, zyz

rng = np.random.default_rng(7)
random_matrix = lambda: np.linalg.qr(rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2)))[0]

print(f"{'gate':8s}{'alpha':>9s}{'theta':>9s}{'beta':>9s}{'rebuild error':>16s}")
for name in ("h", "t", "s", "x"):
    alpha, theta, beta, phase = zyz(gate_matrix(name))
    error = np.max(np.abs(rebuild(alpha, theta, beta, phase) - gate_matrix(name)))
    print(f"{name.upper():8s}{alpha:9.4f}{theta:9.4f}{beta:9.4f}{error:16.2e}")

print()
worst = 0.0
for _ in range(50):
    u = random_matrix()
    alpha, theta, beta, phase = zyz(u)
    worst = max(worst, np.max(np.abs(rebuild(alpha, theta, beta, phase) - u)))
print(f"50 random unitaries, worst rebuild error: {worst:.2e}")

a = np.array([[1, 0], [0, 1j]], dtype=complex)   # S
b = np.array([[1, 0], [0, 1]], dtype=complex)
print()
print(f"S and I differ by {distance_up_to_phase(a, b):.3f} up to phase")
print(f"S and S differ by {distance_up_to_phase(a, a):.2e} up to phase")
