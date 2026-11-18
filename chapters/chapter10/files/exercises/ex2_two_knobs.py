"""Exercise 2 (extend): a second knob, and whether it buys anything.

Add Ry on qubit 0 as well, so the ansatz has two angles. The extra knob can reach states
the one-knob ansatz cannot, and for this Hamiltonian none of them is lower.

Run: python3 chapters/chapter10/files/exercises/ex2_two_knobs.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, Tuple

import numpy as np

import h2


def state_two(theta0: float, theta1: float) -> np.ndarray:
    """Ry on qubit 0, Ry on qubit 1, CNOT from 1 to 0, on |00>."""
    c0, s0 = math.cos(theta0 / 2), math.sin(theta0 / 2)
    c1, s1 = math.cos(theta1 / 2), math.sin(theta1 / 2)
    vector = np.zeros(4, dtype=np.complex128)
    vector[2] = 1.0  # X on qubit 0: the Hartree-Fock string |10>
    ry0 = np.kron(np.array([[c0, -s0], [s0, c0]], dtype=np.complex128), np.eye(2))
    ry1 = np.kron(np.eye(2), np.array([[c1, -s1], [s1, c1]], dtype=np.complex128))
    cnot = np.array(
        [[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]], dtype=np.complex128
    )
    return cnot @ ry1 @ ry0 @ vector


def energy_two(theta0: float, theta1: float) -> float:
    psi = state_two(theta0, theta1)
    return float(np.real(np.vdot(psi, h2.total_with_nuclear() @ psi)))


def best_two(steps: int = 60) -> Tuple[float, float, float]:
    # Seed with the one-knob optimum, so the grid is not the only source of candidates.
    best = (0.0, -0.2235, energy_two(0.0, -0.2235))
    for i in range(steps):
        for j in range(steps):
            t0 = -math.pi + 2 * math.pi * i / (steps - 1)
            t1 = -math.pi + 2 * math.pi * j / (steps - 1)
            value = energy_two(t0, t1)
            if value < best[2]:
                best = (t0, t1, value)
    return best


def checks(check: Callable[[bool, str], None]) -> None:
    exact = h2.exact_ground()
    one_knob = h2.analytic_minimum()[1]

    t0, t1, two_knob = best_two(40)
    check(abs(two_knob - exact) < 1e-4, "two knobs reach the exact ground state")
    check(abs(one_knob - exact) < 1e-9, "and one knob already did")
    check(two_knob <= one_knob + 1e-9, "the extra knob never makes it worse")

    check(abs(energy_two(0.0, 0.0) - h2.energy(0.0)) < 1e-9, "at zero it is Hartree-Fock")
    check(abs(energy_two(0.0, -0.2235) - h2.energy(-0.2235)) < 1e-9,
          "with the first knob at zero it reproduces the one-knob ansatz")

    sampled = [energy_two(0.3, t) for t in (-0.2, 0.0, 0.2)]
    check(len(set(round(value, 9) for value in sampled)) > 1, "the second knob does change the energy somewhere")

    for point in ((0.0, 0.0), (0.3, 0.2), (-1.0, 1.0)):
        check(energy_two(*point) > exact - 1e-9, "no state is below the exact ground state")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
