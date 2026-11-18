"""Exercise 2 (extend): cancel adjacent gates that undo each other.

A circuit written by hand accumulates pairs that cancel: X X, H H, S four times, and
T eight times. A cheap optimizer removes them without touching the unitary.

Run: python3 chapters/chapter03/files/exercises/ex2_cancel.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, List

import numpy as np

from circuit import Circuit, gate_matrix

# How many applications of a gate return the identity.
ORDER = {"x": 2, "y": 2, "z": 2, "h": 2, "s": 4, "t": 8, "cx": 2, "cz": 2}


def cancel(circuit: Circuit) -> Circuit:
    """Remove runs of identical gates on the same wire(s) that multiply to identity."""
    kept: List[list] = []  # [name, wires, theta, count]
    for name, wires, theta in circuit.ops:
        if theta is None and kept and kept[-1][0] == name and kept[-1][1] == wires:
            kept[-1][3] += 1
            order = ORDER.get(name)
            if order is not None and kept[-1][3] % order == 0:
                kept.pop()
            continue
        kept.append([name, wires, theta, 1])

    out = Circuit(circuit.wires)
    for name, wires, theta, _ in kept:
        out.add(name, *wires, theta=theta)
    return out


def checks(check: Callable[[bool, str], None]) -> None:
    x2 = Circuit(1).add("x", 0).add("x", 0)
    check(cancel(x2).gate_count() == 0, "X twice cancels completely")
    check(np.allclose(cancel(x2).unitary(), np.eye(2)), "the cancelled circuit is the identity")

    h3 = Circuit(1).add("h", 0).add("h", 0).add("h", 0)
    check(cancel(h3).gate_count() == 1, "H three times leaves one H")
    check(np.allclose(cancel(h3).unitary(), gate_matrix("h")), "and it is the same unitary")

    s4 = Circuit(1).add("s", 0).add("s", 0).add("s", 0).add("s", 0)
    check(cancel(s4).gate_count() == 0, "S four times cancels")
    check(np.allclose(cancel(s4).unitary(), np.eye(2)), "S four times is the identity")

    t8 = Circuit(1)
    for _ in range(8):
        t8.add("t", 0)
    check(cancel(t8).gate_count() == 0, "T eight times cancels")

    mixed = Circuit(1).add("h", 0).add("x", 0).add("x", 0).add("h", 0)
    check(cancel(mixed).gate_count() == 0, "H X X H cancels through the middle")
    check(np.allclose(cancel(mixed).unitary(), np.eye(2)), "and the unitary is the identity")

    same_wire = Circuit(2).add("x", 0).add("x", 1)
    check(cancel(same_wire).gate_count() == 2, "gates on different wires do not cancel")

    rotated = Circuit(1).add("rz", 0, theta=0.3).add("rz", 0, theta=0.3)
    check(cancel(rotated).gate_count() == 2, "rotations with angles are left alone")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
