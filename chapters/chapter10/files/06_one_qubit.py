"""Demo 06: the same loop on one qubit, where it fits on a postcard.

Run: python3 chapters/chapter10/files/06_one_qubit.py

The Hamiltonian is half Z plus half X. One rotation, two bases, one energy. It is the
whole method with one tenth of the parts, and its minimum is not where either basis alone
would put it.
"""

import cmath
import math
from typing import Dict

import numpy as np

Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
H = 0.5 * Z + 0.5 * X


def state(theta: float) -> np.ndarray:
    return np.array([math.cos(theta / 2), math.sin(theta / 2)], dtype=np.complex128)


def energy(theta: float) -> float:
    psi = state(theta)
    return float(np.real(np.vdot(psi, H @ psi)))


def expectations(theta: float) -> Dict[str, float]:
    psi = state(theta)
    z = float(np.real(np.vdot(psi, Z @ psi)))
    x = float(np.real(np.vdot(psi, X @ psi)))
    return {"Z": z, "X": x, "energy": 0.5 * z + 0.5 * x}


print(f"{'theta':>10s}{'<Z>':>9s}{'<X>':>9s}{'energy':>10s}")
for theta in (0.0, math.pi / 2, math.pi, 1.25 * math.pi):
    row = expectations(theta)
    print(f"{theta:10.4f}{row['Z']:9.4f}{row['X']:9.4f}{row['energy']:10.4f}")

print()
print("at theta = pi the Z reading is at its lowest (-1) and the X reading is zero")
print("the best energy needs both, and it is -0.707 at theta = 1.25 pi")
print()
exact = float(np.linalg.eigvalsh(H)[0])
print(f"the exact ground state of 0.5 Z + 0.5 X is {exact:.6f}")
print(f"and the ansatz reaches {energy(1.25 * math.pi):.6f}")
