"""The same prepared state, indexed by three libraries.

Qiskit numbers amplitudes with qubit 0 as the least significant bit. Cirq and
PennyLane, given wires [0, 1], number them with the first wire as the most
significant. Both are correct; they are different conventions, and a program that
mixes them prints the mirror image of the right answer.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


def numpy_x0() -> np.ndarray:
    """X on wire 0, with wire 0 as the left factor: index 2."""
    return np.kron(np.array([0.0, 1.0]), np.array([1.0, 0.0]))


def numpy_x1() -> np.ndarray:
    """X on wire 1, with wire 1 as the right factor: index 1."""
    return np.kron(np.array([1.0, 0.0]), np.array([0.0, 1.0]))


def qiskit_x0() -> np.ndarray:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    circuit = QuantumCircuit(2)
    circuit.x(0)
    return np.asarray(Statevector.from_instruction(circuit).data, dtype=np.complex128)


def qiskit_x1() -> np.ndarray:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    circuit = QuantumCircuit(2)
    circuit.x(1)
    return np.asarray(Statevector.from_instruction(circuit).data, dtype=np.complex128)


def cirq_x0(qubit_order: str = "big") -> np.ndarray:
    """X on the first Cirq qubit; `big` puts it first in the tensor order."""
    import cirq

    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.X(q0))
    order = [q0, q1] if qubit_order == "big" else [q1, q0]
    result = cirq.Simulator(dtype=np.complex128).simulate(circuit, qubit_order=order)
    return np.asarray(result.final_state_vector, dtype=np.complex128)


def pennylane_x0() -> np.ndarray:
    import pennylane as qml

    device = qml.device("default.qubit", wires=2)

    @qml.qnode(device)
    def circuit():
        qml.PauliX(wires=0)
        return qml.state()

    return np.asarray(circuit(), dtype=np.complex128)


def bell_numpy() -> np.ndarray:
    """(H on wire 0) then CNOT, on |00>, in our own convention."""
    root = 1.0 / np.sqrt(2.0)
    return np.array([root, 0.0, 0.0, root], dtype=np.complex128)


def bell_qiskit() -> np.ndarray:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    return np.asarray(Statevector.from_instruction(circuit).data, dtype=np.complex128)


def bell_cirq() -> np.ndarray:
    import cirq

    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    result = cirq.Simulator(dtype=np.complex128).simulate(circuit, qubit_order=[q0, q1])
    return np.asarray(result.final_state_vector, dtype=np.complex128)


def little_to_big(state: np.ndarray, wires: int = 2) -> np.ndarray:
    """Reindex a little-endian vector as big-endian.

    For two wires the operation is a transpose of the 2x2 amplitude matrix;
    for n wires it is a full reversal of the bit index, which is what the
    `wires` argument generalises to.
    """
    vector = np.asarray(state, dtype=np.complex128)
    expected = 2**wires
    if vector.shape != (expected,):
        raise ValueError(f"a {wires}-wire state has {expected} amplitudes, got {vector.shape}")
    indices = [int(format(i, f"0{wires}b")[::-1], 2) for i in range(expected)]
    out = np.empty_like(vector)
    for source, target in enumerate(indices):
        out[target] = vector[source]
    return out


def comparison() -> List[Tuple[str, np.ndarray, int]]:
    """One prepared state per library, with the index that holds the 1."""
    rows = []
    for name, array in (
        ("numpy (wire 0 left)", numpy_x0()),
        ("qiskit", qiskit_x0()),
        ("pennylane", pennylane_x0()),
        ("cirq (order 0,1)", cirq_x0("big")),
        ("cirq (order 1,0)", cirq_x0("little")),
    ):
        rows.append((name, array, int(np.argmax(np.abs(array)))))
    return rows


def reconciliation() -> Dict[str, float]:
    """Distances after converting Qiskit's order to ours."""
    ours = numpy_x0()
    raw = float(np.max(np.abs(qiskit_x0() - ours)))
    fixed = float(np.max(np.abs(little_to_big(qiskit_x0()) - ours)))
    return {"raw": raw, "after_conversion": fixed}
