"""Demo 02: the Pauli frame, applied in the arithmetic.

Run: python3 chapters/chapter20/files/02_frame.py

The postselect version measures all three qubits and never feeds anything forward. The
two outcome bits become signs in post-processing. The demo simulates the three bases
exactly, applies the frame, and shows the difference between applying it and not.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from teleport import Prepared, bloch, fidelity, postselect
from teleport.circuit import BASES, before_measurement

prepared = Prepared(np.pi / 3, np.pi / 4)
counts = {}
for basis in BASES:
    circuit = before_measurement(prepared)
    if basis == "X":
        circuit.h(2)
    elif basis == "Y":
        circuit.sdg(2)
        circuit.h(2)
    probabilities = Statevector(circuit).probabilities_dict()
    counts[basis] = {key.replace(" ", ""): int(round(p * 100_000)) for key, p in probabilities.items()}

print("marginal of the receiving qubit, per basis:")
for basis in BASES:
    total = sum(counts[basis].values())
    ones = sum(value for key, value in counts[basis].items() if key[0] == "1")
    print(f"  {basis}: p(0) {1 - ones / total:.4f}  p(1) {ones / total:.4f}")

with_frame = bloch(counts, 0.0, 0.0, postselected=True, correct=True)
without = bloch(counts, 0.0, 0.0, postselected=True, correct=False)
print()
print(f"with the frame     bloch {np.round(with_frame, 4)}  F {fidelity(prepared, with_frame):.4f}")
print(f"without the frame  bloch {np.round(without, 4)}  F {fidelity(prepared, without):.4f}")
print()
print("without the frame the four branches average to the maximally mixed state, and")
print("a fidelity of 0.5 is exactly what a random state gives. The bits are the state.")
