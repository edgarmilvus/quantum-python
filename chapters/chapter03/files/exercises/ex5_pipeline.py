"""Exercise 5, file 3 of 3: the wiring.

Runs this chapter's compiler, then Qiskit in the device's real basis, and reports
both. The only file that imports an SDK, and the only one that prints.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

import numpy as np

from circuit import Circuit
from pipeline_core import deeper_than_written, rows, stats
from pipeline_render import render

IBM_BASIS = ["rz", "sx", "x", "cx"]


def qiskit_depth(circuit: Circuit) -> int:
    """Depth after Qiskit's basis translation into the device's gate set."""
    from qiskit import QuantumCircuit, transpile

    qc = QuantumCircuit(circuit.wires)
    for name, wires, theta in circuit.ops:
        if name == "cx":
            qc.cx(*wires)
        elif name == "cz":
            qc.cz(*wires)
        elif theta is None:
            getattr(qc, name)(*wires)
        else:
            getattr(qc, name)(theta, *wires)
    translated = transpile(qc, basis_gates=IBM_BASIS, optimization_level=1)
    return int(translated.depth())


def qiskit_is_equivalent(circuit: Circuit) -> bool:
    from qiskit import QuantumCircuit, transpile
    from qiskit.quantum_info import Operator

    qc = QuantumCircuit(circuit.wires)
    for name, wires, theta in circuit.ops:
        if name == "cx":
            qc.cx(*wires)
        elif name == "cz":
            qc.cz(*wires)
        elif theta is None:
            getattr(qc, name)(*wires)
        else:
            getattr(qc, name)(theta, *wires)
    translated = transpile(qc, basis_gates=IBM_BASIS, optimization_level=1)
    return bool(Operator(translated).equiv(Operator(qc)))


def report(circuit: Circuit, title: str = "compilation report") -> str:
    cost = stats(circuit)
    return render(rows("bell", cost), title)


def checks(check: Callable[[bool, str], None]) -> None:
    bell = Circuit(2).add("h", 0).add("cx", 0, 1)

    cost = stats(bell)
    check(cost["depth_in"] == 2, "the written circuit has depth two")
    check(cost["depth_out"] == 7, "this chapter's compiler reaches depth seven")
    check(abs(cost["ratio"] - 3.5) < 1e-12, "the ratio is 3.5")
    check(cost["distance"] < 1e-12, "the unitary survives")
    check(deeper_than_written(cost), "compilation never shortens this circuit")
    check(stats(bell) == cost, "the pure part is deterministic")

    text = report(bell)
    check("compilation report" in text, "the report has a title")
    check(text.count("\n") >= 5, "four rows and a header")
    check("gates" in text and "depth" in text, "the rows are named")

    qiskit = qiskit_depth(bell)
    check(qiskit >= 2, "Qiskit needs at least the written depth")
    check(qiskit <= cost["depth_out"], "the vendor compiler is at least as compact as a naive one")
    check(qiskit_is_equivalent(bell), "Qiskit's translation preserves the operator")
    check(np.isclose(3.5, cost["ratio"]), "the ratio compares like with like")
