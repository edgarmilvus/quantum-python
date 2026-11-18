"""Chapter 9 harness: orders, the multiplier, phase estimation, and the factors.

Run: python3 chapters/chapter09/files/run_ex9.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import math
import sys
from fractions import Fraction

import numpy as np

import order

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


# -- the classical half -------------------------------------------------
section("orders")
check(order.order_of(2, 15) == 4, "2 has order 4 modulo 15")
check(order.order_of(7, 15) == 4, "7 has order 4 modulo 15")
check(order.order_of(2, 21) == 6, "2 has order 6 modulo 21")
check(order.order_of(2, 35) == 12, "2 has order 12 modulo 35")
check(order.order_of(4, 15) == 2, "4 has order 2 modulo 15")
check(order.order_of(11, 35) == 3, "11 has order 3 modulo 35")
check(order.order_of(2, 7) == 3, "2 has order 3 modulo 7")

try:
    order.order_of(15, 15)
except ValueError:
    check(True, "a multiple of the modulus is refused")
else:
    check(False, "a multiple of the modulus is refused")

check(order.factors_from_order(7, 15, 4) == (3, 5), "r=4 by 7 factors 15")
check(order.factors_from_order(2, 21, 6) == (7, 3), "r=6 by 2 factors 21")
check(order.factors_from_order(11, 35, 3) is None, "an odd order gives nothing")
check(order.factors_from_order(14, 15, 2) is None, "a half that is minus one gives nothing")
check(order.factors_from_order(4, 15, 2) == (3, 5), "a half of four still factors fifteen")

# -- continued fractions ------------------------------------------------
section("continued fractions")
check(order.recover_order(16, 6, 15) == 4, "16/64 recovers the order 4")
check(order.recover_order(32, 6, 15) == 2, "32/64 recovers 2")
check(order.recover_order(48, 6, 15) == 4, "48/64 recovers 4")
check(order.recover_order(0, 6, 15) == 1, "zero recovers order 1")

fraction = order.continued_fraction(21, 6, 15)
check(fraction == Fraction(1, 3), "21/64 is closest to one third")
check(fraction.denominator == 3, "and its denominator is three")

try:
    order.continued_fraction(64, 6, 15)
except ValueError:
    check(True, "k outside the register is refused")
else:
    check(False, "k outside the register is refused")

# -- the permutation ----------------------------------------------------
section("the multiplier")
matrix = order.multiplier_matrix(7, 15, 4)
check(matrix.shape == (16, 16), "four bits give a sixteen-state permutation")
check(np.allclose(matrix.sum(axis=0), 1.0), "every column has one entry")
check(np.allclose(matrix.sum(axis=1), 1.0), "every row has one entry")
check(matrix[1, 1] == 0 and matrix[7, 1] == 1, "the state 1 maps to 7")
check(np.allclose(order.power_matrix(matrix, 4), np.eye(16)), "the fourth power is the identity")
check(np.allclose(order.power_matrix(matrix, 0), np.eye(16)), "the zeroth power is the identity")

try:
    order.multiplier_matrix(6, 15, 4)
except ValueError:
    check(True, "a multiplier that is not coprime is refused")
else:
    check(False, "a multiplier that is not coprime is refused")

# -- phase estimation ---------------------------------------------------
section("phase estimation on the multiplier")
values = order.order_finding(7, 15, 4, 6)
check(abs(sum(values.values()) - 1.0) < 1e-9, "the distribution sums to one")
nonzero = {k: p for k, p in values.items() if p > 1e-9}
check(len(nonzero) == 4, "four outcomes carry the probability")
check(all(abs(p - 0.25) < 1e-9 for p in nonzero.values()), "each holds a quarter")
check(set(nonzero) == {0, 16, 32, 48}, "and they are the multiples of sixteen")
check(order.recover_order(16, 6, 15) == 4, "the first useful one recovers the order")

retry = order.attempt(7, 15, 32, 6)
check(retry["r"] == 2, "the second outcome recovers order two")
check(retry["factors"] is None, "which fails, and the algorithm retries")

good = order.attempt(7, 15, 16, 6)
check(good["factors"] == (3, 5), "the first outcome gives the factors")

# -- success rates ------------------------------------------------------
section("success rates")
for n, a, bits, ancillas, expected in (
    (15, 7, 4, 6, 0.5),
    (21, 2, 5, 8, 0.2856),
    (35, 2, 6, 10, 0.2992),
):
    success = order.quantum_success(a, n, bits, ancillas)
    check(abs(success["probability"] - expected) < 0.001, f"N={n}: one run succeeds {expected}")
    check(0.2 < success["probability"] < 0.6, f"N={n}: the rate is between a fifth and three fifths")

# -- resources ----------------------------------------------------------
section("resources")
row = order.circuit_resources(15)
check(row == {"n": 15, "bits": 4, "ancillas": 8, "qubits": 12, "multiplications": 36},
      "fifteen needs twelve qubits and thirty-six multiplications")
big = order.circuit_resources(2048)
check(big["qubits"] == 36, "a 2048-bit modulus needs thirty-six qubits of arithmetic")
check(big["multiplications"] == 300, "and three hundred multiplications")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
