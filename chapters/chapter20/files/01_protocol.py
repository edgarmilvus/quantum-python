"""Demo 01: the four branches, and the correction each one needs.

Run: python3 chapters/chapter20/files/01_protocol.py

Before the measurement, the state is a sum of four branches. In branch (m0, m1) the
receiving qubit holds X^m1 Z^m0 applied to the state we sent. The demo computes all
four and proves the correction returns the original with fidelity 1.0 on a statevector.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from teleport import Prepared
from teleport.circuit import before_measurement

prepared = Prepared(np.pi / 3, np.pi / 4)
one = QuantumCircuit(1)
one.u(prepared.theta, prepared.phi, 0.0, 0)
psi = Statevector.from_int(0, 2).evolve(one).data

state = Statevector(before_measurement(prepared)).data
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)

print(f"prepared {prepared.report()}")
print(f"{'m0':>2s}{'m1':>3s}   branch state            corrected   fidelity")
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
        overlap = abs(np.vdot(psi, corrected)) ** 2
        print(f"{m0:2d}{m1:3d}   {np.round(received, 3)}   {np.round(corrected, 3)}   {overlap:.4f}")

print()
print("every branch carries the same state, up to a Pauli; the two classical bits")
print("say which Pauli, and the correction is X for m1 and Z for m0.")
