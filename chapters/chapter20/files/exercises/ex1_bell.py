"""Exercise 1 (repair): a Bell pair that was never entangled.

Run: python3 chapters/chapter20/files/exercises/ex1_bell.py

The protocol entangles qubits 1 and 2 with a Hadamard on qubit 1 and a CNOT onto qubit 2.
Drop the Hadamard and the pair is a product state: the branches no longer carry the
prepared state, and one of them still looks half right, which is why the defect survives
a glance at a single histogram.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, List

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from teleport import Prepared
from teleport.circuit import before_measurement


def broken(prepared: Prepared) -> QuantumCircuit:
    """The defect: the Bell pair is two independent qubits."""
    qc = QuantumCircuit(3)
    qc.u(prepared.theta, prepared.phi, 0.0, 0)
    qc.cx(1, 2)
    qc.cx(0, 1)
    qc.h(0)
    return qc


def branch_fidelities(circuit: QuantumCircuit, prepared: Prepared) -> List[float]:
    one = QuantumCircuit(1)
    one.u(prepared.theta, prepared.phi, 0.0, 0)
    psi = Statevector.from_int(0, 2).evolve(one).data
    state = Statevector(circuit).data
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    out = []
    for m0 in (0, 1):
        for m1 in (0, 1):
            branch = np.zeros(8, dtype=complex)
            for index, amplitude in enumerate(state):
                if (index & 1) == m0 and ((index >> 1) & 1) == m1:
                    branch[index] = amplitude
            branch /= np.linalg.norm(branch)
            base = m0 | (m1 << 1)
            received = np.array([branch[base], branch[base + 4]])
            received /= np.linalg.norm(received)
            corrected = received.copy()
            if m0:
                corrected = Z @ corrected
            if m1:
                corrected = X @ corrected
            out.append(float(abs(np.vdot(psi, corrected)) ** 2))
    return out


def checks(check: Callable[[bool, str], None]) -> None:
    prepared = Prepared(math.pi / 3, math.pi / 4)
    good = branch_fidelities(before_measurement(prepared), prepared)
    bad = branch_fidelities(broken(prepared), prepared)

    check(all(abs(value - 1.0) < 1e-9 for value in good), "the correct circuit returns the state in every branch")
    check(len(bad) == 4, "the defect still has four branches")
    check(abs(bad[0] - 0.75) < 1e-6, "the first branch is 0.75, which looks like a partial success")
    check(abs(bad[1] - 0.25) < 1e-6, "the second is 0.25")
    check(abs(sum(bad) / 4 - 0.5) < 1e-6, "the four branches average to a coin flip")
    check(max(bad) < 0.8, "no branch of the defect is close to one")
    check(min(good) - max(bad) > 0.2, "the gap between the two circuits is large")

    check(broken(prepared).count_ops().get("h", 0) == 1, "the defect has one Hadamard fewer")
    check(before_measurement(prepared).count_ops().get("h", 0) == 2, "the correct circuit has two")
    check(before_measurement(prepared).num_qubits == 3, "three qubits either way")

    entangled = Statevector(before_measurement(prepared))
    check(entangled.num_qubits == 3, "the state is three qubits")
    check(abs(abs(entangled.data[0]) ** 2 * 4 - 1) < 0.5, "the correct state has weight on four outcomes")

    product = Statevector(broken(prepared))
    check(abs(product.data[0]) > 0, "and the defect still starts from a basis state")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
