"""A circuit as a list of gates, and the two numbers that describe it.

`unitary()` answers what the circuit computes. `depth()` answers how long it takes
in sequential steps. They are independent, and confusing them is the defect this
chapter is about.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np

I2 = np.eye(2, dtype=np.complex128)
X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)
S = np.array([[1, 0], [0, 1j]], dtype=np.complex128)
T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=np.complex128)
SX = 0.5 * np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]], dtype=np.complex128)

FIXED = {"i": I2, "x": X, "y": Y, "z": Z, "h": H, "s": S, "t": T, "sx": SX}


def rotation(axis: str, theta: float) -> np.ndarray:
    cosine, sine = np.cos(theta / 2), np.sin(theta / 2)
    if axis == "x":
        return np.array([[cosine, -1j * sine], [-1j * sine, cosine]], dtype=np.complex128)
    if axis == "y":
        return np.array([[cosine, -sine], [sine, cosine]], dtype=np.complex128)
    if axis == "z":
        return np.array(
            [[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]], dtype=np.complex128
        )
    raise ValueError(f"axis must be x, y or z, got {axis!r}")


def gate_matrix(name: str, theta: Optional[float] = None) -> np.ndarray:
    if name in ("rx", "ry", "rz"):
        if theta is None:
            raise ValueError(f"{name} needs an angle")
        return rotation(name[1], theta)
    if name not in FIXED:
        raise ValueError(f"unknown gate {name!r}")
    if theta is not None:
        raise ValueError(f"{name} takes no angle")
    return FIXED[name]


Op = Tuple[str, Tuple[int, ...], Optional[float]]


class Circuit:
    """Gates applied in order, on a fixed number of wires.

    An op is (name, wires, theta). Names are the fixed gates, the three rotations,
    and the two controlled gates cx and cz.
    """

    def __init__(self, wires: int, ops: Optional[Iterable[Op]] = None) -> None:
        if wires < 1:
            raise ValueError(f"a circuit has at least one wire, got {wires}")
        self._wires = wires
        self._ops: List[Op] = []
        for name, op_wires, theta in ops or []:
            self.add(name, *op_wires, theta=theta)

    # -- construction ----------------------------------------------------
    def add(self, name: str, *wires: int, theta: Optional[float] = None) -> "Circuit":
        expected = 2 if name in ("cx", "cz") else 1
        if len(wires) != expected:
            raise ValueError(f"{name} acts on {expected} wire(s), got {len(wires)}")
        for wire in wires:
            if not 0 <= wire < self._wires:
                raise ValueError(f"wire must be in [0, {self._wires - 1}], got {wire}")
        if name in ("cx", "cz") and wires[0] == wires[1]:
            raise ValueError(f"{name} needs two different wires, got {wires[0]} twice")
        if name not in ("cx", "cz") and name not in FIXED and name not in ("rx", "ry", "rz"):
            raise ValueError(f"unknown gate {name!r}")
        if name in ("rx", "ry", "rz") and theta is None:
            raise ValueError(f"{name} needs an angle")
        if name in FIXED and theta is not None:
            raise ValueError(f"{name} takes no angle, got {theta}")
        self._ops.append((name, tuple(wires), theta))
        return self

    def copy(self) -> "Circuit":
        return Circuit(self._wires, self._ops)

    # -- properties ------------------------------------------------------
    @property
    def ops(self) -> List[Op]:
        return list(self._ops)

    @property
    def wires(self) -> int:
        return self._wires

    def gate_count(self) -> int:
        return len(self._ops)

    def depth(self) -> int:
        """The number of sequential layers: gates on disjoint wires share one."""
        free_at = [0] * self._wires
        for _, wires, _ in self._ops:
            layer = max(free_at[w] for w in wires) + 1
            for w in wires:
                free_at[w] = layer
        return max(free_at) if self._ops else 0

    def layers(self) -> List[List[Op]]:
        free_at = [0] * self._wires
        depth = 0
        placed: List[Tuple[int, Op]] = []
        for op in self._ops:
            _, wires, _ = op
            layer = max(free_at[w] for w in wires) + 1
            for w in wires:
                free_at[w] = layer
            placed.append((layer, op))
            depth = max(depth, layer)
        result: List[List[Op]] = [[] for _ in range(depth)]
        for layer, op in placed:
            result[layer - 1].append(op)
        return result

    # -- computation -----------------------------------------------------
    def matrix(self, op: Op) -> np.ndarray:
        name, wires, theta = op
        if name in ("cx", "cz"):
            return self._embed_two(name, wires)
        return self._embed_one(gate_matrix(name, theta), wires[0])

    def _embed_one(self, gate: np.ndarray, wire: int) -> np.ndarray:
        factors = [I2] * self._wires
        factors[wire] = gate
        matrix = factors[0]
        for factor in factors[1:]:
            matrix = np.kron(matrix, factor)
        return matrix

    def _embed_two(self, name: str, wires: Sequence[int]) -> np.ndarray:
        control, target = wires
        size = 2**self._wires
        matrix = np.zeros((size, size), dtype=np.complex128)
        for column in range(size):
            bits = [int(b) for b in format(column, f"0{self._wires}b")]
            row_bits = list(bits)
            if bits[control] == 1:
                if name == "cx":
                    row_bits[target] ^= 1
                else:  # cz flips the sign instead of the bit
                    if bits[target] == 1:
                        matrix[column, column] = -1.0
                        continue
            row = int("".join(str(b) for b in row_bits), 2)
            matrix[row, column] = 1.0
        return matrix

    def unitary(self) -> np.ndarray:
        total = np.eye(2**self._wires, dtype=np.complex128)
        for op in self._ops:
            total = self.matrix(op) @ total
        return total

    def is_unitary(self, tol: float = 1e-12) -> bool:
        u = self.unitary()
        return bool(np.max(np.abs(u.conj().T @ u - np.eye(u.shape[0]))) < tol)

    def __len__(self) -> int:
        return len(self._ops)

    def __repr__(self) -> str:
        body = ", ".join(f"{n}{list(w)}" for n, w, _ in self._ops)
        return f"Circuit({self._wires} wires: {body})"
