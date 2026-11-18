"""Exercise 2 (extend): a constraint is a penalty, and a penalty has a price.

Run: python3 chapters/chapter14/files/exercises/ex2_penalty.py

"At most one vertex on side 1" is not a graph property, so it cannot go into the
cut. It goes into the energy as a penalty per chosen pair. The penalty is a free
parameter with a sharp threshold: at 0.9 the unconstrained optimum survives, at
1.0 the constraint takes over, and the transition is exactly where the gain from
one more chosen vertex equals the pair it costs.
"""

import itertools
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List, Tuple

from anneal import instances, qubo


def constrained(edges, n: int, strength: float) -> Dict:
    """The cut QUBO plus a penalty for every pair of chosen vertices."""
    base = qubo.qubo_from_maxcut(edges, n)
    penalty = qubo.penalty_qubo(n, range(n), strength)
    return qubo.add(base, penalty)


def best_with(edges, n: int, strength: float) -> Tuple[float, int, int]:
    """The optimum, the number of chosen vertices, and the bitmask."""
    problem = constrained(edges, n, strength)
    value, assignment = qubo.brute_force(problem, n)
    bits = sum(bit << index for index, bit in assignment.items())
    return value, sum(assignment.values()), bits


def threshold(edges, n: int, limit: float = 5.0, step: float = 0.01) -> float:
    """The smallest penalty at which the constrained optimum has one vertex."""
    strength = step
    while strength <= limit:
        _, chosen, _ = best_with(edges, n, strength)
        if chosen == 1:
            return round(strength, 2)
        strength += step
    raise ValueError(f"no threshold below {limit}")


def checks(check: Callable[[bool, str], None]) -> None:
    edges = instances.maxcut_square()
    n = 4

    value, chosen, bits = best_with(edges, n, 0.0)
    check(value == -4.0, "with no penalty the optimum is the unconstrained cut")
    check(chosen == 2, "which puts two vertices on side 1")
    check(bits in (0b0101, 0b1010), "at one of the two optimal assignments")

    value, chosen, bits = best_with(edges, n, 0.9)
    check(chosen == 2, "a penalty of 0.9 still allows two chosen")
    check(abs(value + 3.1) < 1e-9, "at energy -3.10")

    value, chosen, bits = best_with(edges, n, 1.1)
    check(chosen == 1, "a penalty of 1.1 allows only one")
    check(bits in (0b0001, 0b0010, 0b0100, 0b1000), "and the vertex chosen is a single one")
    check(abs(value + 3.0) < 1e-9, "at energy -3.00, which is a cut of 3")

    check(threshold(edges, n) == 1.0, "the threshold is exactly 1.0")

    # The threshold is the gain from the second vertex, which is one edge.
    best_pair = max(
        qubo.energy(qubo.qubo_from_maxcut(edges, n), {i: (bits >> i) & 1 for i in range(n)})
        for bits in range(16)
        if bin(bits).count("1") == 2
    )
    best_single = max(
        qubo.energy(qubo.qubo_from_maxcut(edges, n), {i: (bits >> i) & 1 for i in range(n)})
        for bits in range(16)
        if bin(bits).count("1") == 1
    )
    check(abs((best_single - best_pair) - 1.0) < 1e-12,
          "and it equals the energy the second vertex buys, which is one")

    check(len(qubo.penalty_qubo(n, range(n), 0.0)) == 6, "a zero penalty is a no-op with six terms")
    try:
        qubo.penalty_qubo(n, range(n), -1.0)
    except ValueError:
        check(True, "a negative penalty is refused")
    else:
        check(False, "a negative penalty is refused")

    try:
        qubo.penalty_qubo(n, [0], 1.0)
    except ValueError:
        check(True, "a pair penalty over one variable is refused")
    else:
        check(False, "a pair penalty over one variable is refused")

    check(len(qubo.penalty_qubo(n, range(3), 1.0)) == 3, "three variables make three pairs")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
