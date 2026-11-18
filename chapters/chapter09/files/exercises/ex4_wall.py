"""Exercise 4 (break): the size at which the chapter's own simulator dies.

The textbook circuit needs about three qubits per bit of the modulus, and the state is
2^(3 bits) amplitudes. The exercise finds the modulus at which the state stops fitting,
and shows that it is far below a real key.

Run: python3 chapters/chapter09/files/exercises/ex4_wall.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, Dict, List

import order

BYTES = 16
GIB = 1024**3


def state_bytes(n: int) -> int:
    row = order.circuit_resources(n)
    return (1 << row["qubits"]) * BYTES


def first_above(limit_bytes: int, max_bits: int = 40) -> int:
    if limit_bytes <= 0:
        raise ValueError(f"a limit must be positive, got {limit_bytes}")
    for bits in range(1, max_bits + 1):
        n = (1 << bits) - 1
        if state_bytes(n) > limit_bytes:
            return n
    raise ValueError(f"no modulus crosses {limit_bytes}")


def table(moduli: List[int]) -> List[Dict[str, float]]:
    return [
        {
            "n": n,
            "qubits": order.circuit_resources(n)["qubits"],
            "gib": state_bytes(n) / GIB,
        }
        for n in moduli
    ]


def checks(check: Callable[[bool, str], None]) -> None:
    check(state_bytes(15) == 4096 * 16, "fifteen needs four thousand amplitudes")
    check(abs(state_bytes(21) / GIB) < 1e-2, "twenty-one is still tiny")
    check(order.circuit_resources(2048)["qubits"] == 36, "a 2048-bit modulus needs 36 qubits")

    check(abs(state_bytes(2048) / GIB - 1024.0) < 1e-6, "and a tebibyte of state")
    check(first_above(GIB) < 2048, "a gibibyte is crossed well below a 2048-bit modulus")

    rows = table([15, 21, 2048])
    check(len(rows) == 3, "three rows")
    check(rows[-1]["gib"] == 1024.0, "the last row is a tebibyte")

    check(first_above(16 * GIB) < 2048, "sixteen gibibytes arrives before a 2048-bit modulus")

    for bad in (0, -1):
        try:
            first_above(bad)
        except ValueError:
            check(True, f"limit {bad} is refused")
        else:
            check(False, f"limit {bad} is refused")

    check(state_bytes(63) < state_bytes(127), "more bits mean more state")
    check(math.ceil(math.log2(2048 + 1)) == order.circuit_resources(2048)["bits"],
          "the bit count is the ceiling of the log")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
