"""The same two numbers, held by three SDKs.

Nothing in this module teaches quantum mechanics. It answers one question a
reader will ask on page one: if I already have the array, why do I need Qiskit,
PennyLane or Cirq at all? The answer is that each of them will hold that array
inside a larger machine, and the three must agree on it.
"""

from __future__ import annotations

from typing import Iterable, List

import numpy as np


def _amps(amplitudes: Iterable[complex]) -> np.ndarray:
    values = np.asarray(list(amplitudes), dtype=np.complex128)
    if values.shape != (2,):
        raise ValueError(f"expected 2 amplitudes, got shape {values.shape}")
    return values


def qiskit_statevector(amplitudes: Iterable[complex]) -> np.ndarray:
    """Prepare the state with a Qiskit circuit, then read it back out."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    values = _amps(amplitudes)
    circuit = QuantumCircuit(1)
    circuit.initialize(values, 0)
    return np.asarray(Statevector.from_instruction(circuit).data, dtype=np.complex128)


def pennylane_statevector(amplitudes: Iterable[complex]) -> np.ndarray:
    """Prepare the state with a PennyLane QNode on the default simulator."""
    import pennylane as qml

    values = _amps(amplitudes)
    device = qml.device("default.qubit", wires=1)

    @qml.qnode(device)
    def circuit(amps):
        qml.StatePrep(amps, wires=0)
        return qml.state()

    return np.asarray(circuit(values), dtype=np.complex128)


def cirq_statevector(amplitudes: Iterable[complex]) -> np.ndarray:
    """Load the state as an initial state vector into a Cirq simulator."""
    import cirq

    values = _amps(amplitudes)
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit()
    result = cirq.Simulator(dtype=np.complex128).simulate(
        circuit, qubit_order=[qubit], initial_state=values
    )
    return np.asarray(result.final_state_vector, dtype=np.complex128)


IMPLEMENTATIONS = {
    "numpy": lambda amps: np.asarray(list(amps), dtype=np.complex128),
    "qiskit": qiskit_statevector,
    "pennylane": pennylane_statevector,
    "cirq": cirq_statevector,
}


def compare(
    amplitudes: Iterable[complex], atol: float = 1e-9
) -> List[tuple[str, np.ndarray, float]]:
    """Run one state through every implementation and measure the disagreement.

    The reference is the plain array, because it is the object the other three
    are supposed to be holding. The returned distance is the largest absolute
    difference against that reference.
    """
    values = _amps(amplitudes)
    rows = []
    for name, fn in IMPLEMENTATIONS.items():
        produced = fn(values)
        distance = float(np.max(np.abs(produced - values)))
        rows.append((name, produced, distance))
    return rows
