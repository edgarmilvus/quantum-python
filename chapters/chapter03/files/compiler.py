"""Rewriting a circuit into a basis, and counting what the rewrite costs.

The compiler does one thing: replace every gate the target does not have with a
sequence it does have, keeping the unitary. The cost is depth, and the chapter
measures it rather than asserting it.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from circuit import Circuit, H, gate_matrix
from decompose import distance_up_to_phase, zyz

BASIS_1Q = ("rz", "ry")
BASIS_2Q = "cz"


def compile_1q(name: str, theta=None) -> List[Tuple[str, float]]:
    """One gate as (rz, ry, rz): three rotations, same unitary up to phase.

    ZYZ returns U = Rz(alpha) Ry(theta) Rz(beta), and a circuit applies its gates
    in order, so beta is written first and alpha last.
    """
    matrix = gate_matrix(name, theta)
    alpha, middle, beta, _ = zyz(matrix)
    return [("rz", beta), ("ry", middle), ("rz", alpha)]


def compile_cx() -> List[Tuple[str, object]]:
    """A controlled-NOT written with the controlled-Z the backend has.

    H on the target, CZ, H on the target: the two Hadamards turn the sign flip
    into a bit flip. The Hadamards are themselves three rotations each, so one
    CX costs seven gates in this basis.
    """
    return [("h", 1), ("cz", None), ("h", 1)]


def compile_circuit(circuit: Circuit) -> Circuit:
    """Rewrite every gate into BASIS_1Q plus CZ."""
    if circuit.wires < 1:
        raise ValueError("a circuit has at least one wire")
    out = Circuit(circuit.wires)
    for name, wires, theta in circuit.ops:
        if name in BASIS_1Q:
            out.add(name, wires[0], theta=theta)
            continue
        if name == "cz":
            out.add("cz", *wires)
            continue
        if name == "cx":
            control, target = wires
            for gate_name, angle in compile_1q("h"):
                out.add(gate_name, target, theta=angle)
            out.add("cz", control, target)
            for gate_name, angle in compile_1q("h"):
                out.add(gate_name, target, theta=angle)
            continue
        for gate_name, angle in compile_1q(name, theta):
            out.add(gate_name, wires[0], theta=angle)
    return out


H_NAME = "h"


def compiled_cost(circuit: Circuit) -> dict:
    """Depth, gate count and the ratio, before and after compilation."""
    after = compile_circuit(circuit)
    before_depth = circuit.depth()
    after_depth = after.depth()
    return {
        "ops_before": circuit.gate_count(),
        "ops_after": after.gate_count(),
        "depth_before": before_depth,
        "depth_after": after_depth,
        "depth_ratio": (after_depth / before_depth) if before_depth else float("nan"),
        "distance": distance_up_to_phase(circuit.unitary(), after.unitary()),
    }


def check_basis(circuit: Circuit) -> List[str]:
    """The names in a circuit that the basis does not provide."""
    allowed = set(BASIS_1Q) | {BASIS_2Q}
    return sorted({name for name, _, _ in circuit.ops if name not in allowed})
