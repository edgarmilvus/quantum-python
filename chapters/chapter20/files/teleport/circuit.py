"""The teleportation circuit, in two versions that must agree.

The protocol is three qubits and two classical bits: prepare the state on qubit 0,
share a Bell pair between qubits 1 and 2, measure qubits 0 and 1 in the Bell basis,
and correct qubit 2 with an X and a Z chosen by those two outcomes.

The dynamic version lets the device apply the correction inside the same circuit. The
postselect version measures everything and applies the correction in the arithmetic,
which is the control: it uses no mid-circuit feedback and it says what the same hardware
would do without it.
"""

from __future__ import annotations

from typing import List

from qiskit import QuantumCircuit

from .state import Prepared

BASES = ("X", "Y", "Z")


def rotate_for(qubit: int, basis: str) -> QuantumCircuit:
    """The rotation that turns a measurement in `basis` into a computational one."""
    if basis not in BASES:
        raise ValueError(f"a basis is one of {BASES}, got {basis!r}")
    qc = QuantumCircuit(1, name=f"tomography-{basis}")
    if basis == "X":
        qc.h(0)
    elif basis == "Y":
        qc.sdg(0)
        qc.h(0)
    return qc


def before_measurement(prepared: Prepared) -> QuantumCircuit:
    """The three-qubit state just before the Bell measurement, with no measurement."""
    qc = QuantumCircuit(3, name="before-measurement")
    qc.u(prepared.theta, prepared.phi, 0.0, 0)
    qc.h(1)
    qc.cx(1, 2)
    qc.cx(0, 1)
    qc.h(0)
    return qc


def teleport(prepared: Prepared, basis: str = "Z", dynamic: bool = True, correct: bool = True) -> QuantumCircuit:
    """One teleportation circuit, ending in a measurement of the receiving qubit.

    `dynamic=False` leaves the correction to the arithmetic; `correct=False` omits it
    altogether, which is the control that shows what the two classical bits buy.
    """
    kind = "dynamic" if dynamic and correct else ("uncorrected" if not correct else "postselect")
    qc = QuantumCircuit(3, 3, name=f"teleport-{basis}-{kind}")
    qc.u(prepared.theta, prepared.phi, 0.0, 0)
    qc.h(1)
    qc.cx(1, 2)
    qc.cx(0, 1)
    qc.h(0)
    qc.measure(0, 0)
    qc.measure(1, 1)
    if dynamic and correct:
        with qc.if_test((qc.clbits[1], 1)):
            qc.x(2)
        with qc.if_test((qc.clbits[0], 1)):
            qc.z(2)
    qc.compose(rotate_for(2, basis), inplace=True, qubits=[2])
    qc.measure(2, 2)
    return qc


def tomography(prepared: Prepared, dynamic: bool = True, correct: bool = True) -> List[QuantumCircuit]:
    """The three circuits the Bloch vector needs."""
    return [teleport(prepared, basis, dynamic, correct) for basis in BASES]


def calibration() -> List[QuantumCircuit]:
    """All zeros, then one circuit per qubit prepared in |1>: four circuits."""
    circuits = []
    zeros = QuantumCircuit(3, 3)
    zeros.measure([0, 1, 2], [0, 1, 2])
    circuits.append(zeros)
    for qubit in range(3):
        qc = QuantumCircuit(3, 3)
        qc.x(qubit)
        qc.measure([0, 1, 2], [0, 1, 2])
        circuits.append(qc)
    return circuits
