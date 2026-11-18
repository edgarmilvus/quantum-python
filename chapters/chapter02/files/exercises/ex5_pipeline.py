"""Exercise 5, file 3 of 3: the wiring.

The only file that knows about SDKs, and the only one that prints. It runs the
same gate list through the hand-written pipeline and through two libraries, then
reports the distance. It contains no matrix arithmetic of its own.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

# Allow `python3 ex3_shots.py` from this directory: the exercise imports
# modules that live one level up.
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List, Sequence

import numpy as np

from pipeline_core import Gate, final_state, matrix, probability_rows
from pipeline_render import render

BELL: List[Gate] = [("H", 0), ("CNOT", 0)]


def run_local(gates: Sequence[Gate]) -> np.ndarray:
    return final_state(gates)


def run_qiskit(gates: Sequence[Gate]) -> np.ndarray:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    circuit = QuantumCircuit(2)
    for name, wire in gates:
        if name == "CNOT":
            circuit.cx(0, 1)
        else:
            getattr(circuit, name.lower())(wire)
    return np.asarray(Statevector.from_instruction(circuit).data, dtype=np.complex128)


def run_cirq(gates: Sequence[Gate]) -> np.ndarray:
    import cirq

    q0, q1 = cirq.LineQubit.range(2)
    qubits = [q0, q1]
    circuit = cirq.Circuit()
    for name, wire in gates:
        if name == "CNOT":
            circuit.append(cirq.CNOT(q0, q1))
        else:
            circuit.append(getattr(cirq, name)(qubits[wire]))
    result = cirq.Simulator(dtype=np.complex128).simulate(circuit, qubit_order=qubits)
    return np.asarray(result.final_state_vector, dtype=np.complex128)


def report(gates: Sequence[Gate] = BELL, title: str = "pipeline") -> str:
    local = run_local(gates)
    return render(probability_rows(local), title)


def distances(gates: Sequence[Gate] = BELL) -> Dict[str, float]:
    """Distance of each library from the local pipeline, after reordering.

    Qiskit is little-endian, so its vector is converted before comparison; Cirq
    is asked for the order (0, 1), which already matches this chapter.
    """
    from ordering import little_to_big

    local = np.asarray(run_local(gates), dtype=np.complex128)
    qk = little_to_big(np.asarray(run_qiskit(gates), dtype=np.complex128))
    cq = np.asarray(run_cirq(gates), dtype=np.complex128)
    return {
        "qiskit": float(np.max(np.abs(qk - local))),
        "cirq": float(np.max(np.abs(cq - local))),
    }


def checks(check: Callable[[bool, str], None]) -> None:
    state = run_local(BELL)
    check(state.shape == (4,), "the pipeline returns four amplitudes")
    check(abs(np.sum(np.abs(state) ** 2) - 1.0) < 1e-12, "the result is normalized")
    check(abs(abs(state[0]) ** 2 - 0.5) < 1e-12, "half the probability is at |00>")
    check(abs(abs(state[3]) ** 2 - 0.5) < 1e-12, "half the probability is at |11>")

    rows = probability_rows(state)
    check(len(rows) == 4, "one row per amplitude")
    check(rows[0][0] == "00" and rows[3][0] == "11", "the labels are two-bit strings")
    check(abs(sum(row[1] for row in rows) - 1.0) < 1e-12, "the rows sum to one")

    text = report()
    check("pipeline" in text and "00" in text and "11" in text, "the report names its states")
    check(text.count("\n") >= 5, "the report has a title, a header and four rows")

    check(np.allclose(matrix(BELL), matrix(BELL)), "the pure part is deterministic")
    check(np.allclose(final_state([("X", 0)]), np.array([0, 0, 1, 0])), "X on wire 0 is index 2 in this pipeline")

    distances_ = distances()
    check(distances_["qiskit"] < 1e-9, "Qiskit matches after the endianness conversion")
    check(distances_["cirq"] < 1e-9, "Cirq matches with its own order")

    try:
        matrix([("CNOT", 1)])
    except ValueError:
        check(True, "CNOT on wire 1 is refused in this exercise")
    else:
        check(False, "CNOT on wire 1 is refused in this exercise")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
