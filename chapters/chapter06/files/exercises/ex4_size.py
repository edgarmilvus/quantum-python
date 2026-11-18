"""Exercise 4 (break): the size at which the permutation matrix stops fitting.

An oracle as a matrix is 2^(n+1) squared complex numbers. That is fine at four bits and
impossible at fifteen, and the crossing is arithmetic.

Run: python3 chapters/chapter06/files/exercises/ex4_size.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

BYTES_PER_ENTRY = 16  # complex128
GIB = 1024**3


def matrix_bytes(n: int) -> int:
    if n < 1:
        raise ValueError(f"an oracle needs at least one input bit, got {n}")
    side = 1 << (n + 1)
    return side * side * BYTES_PER_ENTRY


def amplitudes(n: int) -> int:
    return 1 << (n + 1)


def first_size_above(limit_bytes: int, max_bits: int = 40) -> int:
    if limit_bytes <= 0:
        raise ValueError(f"a limit must be positive, got {limit_bytes}")
    for n in range(1, max_bits + 1):
        if matrix_bytes(n) > limit_bytes:
            return n
    raise ValueError(f"no size crosses {limit_bytes} within {max_bits} bits")


def table(sizes: List[int]) -> List[Dict[str, float]]:
    return [{"n": n, "amplitudes": amplitudes(n), "gib": matrix_bytes(n) / GIB} for n in sizes]


def checks(check: Callable[[bool, str], None]) -> None:
    check(amplitudes(1) == 4, "one bit needs four amplitudes")
    check(amplitudes(4) == 32, "four bits need thirty-two")
    check(matrix_bytes(4) == 32 * 32 * 16, "the matrix at four bits is 16 KiB")
    check(matrix_bytes(10) == (1 << 11) ** 2 * 16, "at ten bits it is 64 MiB")

    check(abs(matrix_bytes(14) / GIB - 16.0) < 1e-9, "at fourteen bits it is exactly 16 GiB")
    check(abs(matrix_bytes(15) / GIB - 64.0) < 1e-9, "at fifteen it is 64 GiB")

    crossing = first_size_above(16 * GIB)
    check(crossing == 15, "the first size above 16 GiB is fifteen bits")
    check(first_size_above(GIB) == 13, "the first size above 1 GiB is thirteen bits")

    rows = table([4, 10, 14, 15])
    check(len(rows) == 4, "the table has four rows")
    check(rows[-1]["gib"] > 32, "the last row is above thirty-two GiB")

    try:
        matrix_bytes(0)
    except ValueError:
        check(True, "zero bits are refused")
    else:
        check(False, "zero bits are refused")

    try:
        first_size_above(0)
    except ValueError:
        check(True, "a zero limit is refused")
    else:
        check(False, "a zero limit is refused")

    check(matrix_bytes(6) * 4 == matrix_bytes(7), "each bit quadruples the matrix")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
