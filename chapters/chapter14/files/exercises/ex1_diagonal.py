"""Exercise 1 (repair): a QUBO that forgot its diagonal.

Run: python3 chapters/chapter14/files/exercises/ex1_diagonal.py

The MaxCut QUBO has -degree on the diagonal and 2w off it. Keeping only the
off-diagonal terms gives an energy that is not minus the cut: at the optimal
assignment it reads +2 instead of -4, and its minimum is 0 at the all-zero
assignment, which is the worst cut the graph has.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from anneal import instances, qubo


def without_diagonal(pairs: Dict) -> Dict:
    """The defect: only the pairwise terms survive."""
    return {key: value for key, value in pairs.items() if key[0] != key[1]}


def cut_of(bits: int, edges) -> float:
    return sum(weight for i, j, weight in edges if ((bits >> i) & 1) != ((bits >> j) & 1))


def checks(check: Callable[[bool, str], None]) -> None:
    edges = instances.maxcut_square()
    correct = qubo.qubo_from_maxcut(edges, 4)
    broken = without_diagonal(correct)

    check(len(correct) == 9 and len(broken) == 5, "four diagonal terms were dropped")
    check(len([key for key in correct if key[0] == key[1]]) == 4, "the correct QUBO has four")

    good = qubo.all_energies(correct, 4)
    bad = qubo.all_energies(broken, 4)

    for bits in range(16):
        check_here = abs(good[bits] + cut_of(bits, edges)) < 1e-12
        if not check_here:
            check(False, f"the correct energy matches the cut at {bits:04b}")
    check(True, "the correct energy matches the cut on all sixteen")

    check(abs(bad[0b0101] - 2.0) < 1e-12, "the defect reads +2 where the cut is 4")
    check(abs(good[0b0101] + 4.0) < 1e-12, "and the correct QUBO reads -4")

    best_bad, assignment_bad = qubo.brute_force(broken, 4)
    best_good, _ = qubo.brute_force(correct, 4)
    check(best_bad == 0.0, "the defect's minimum is zero")
    check(best_good == -4.0, "the correct minimum is -4")
    check(sum(assignment_bad.values()) == 0, "and the defect's optimum is the all-zero assignment")
    check(cut_of(0, edges) == 0.0, "which cuts nothing")

    # The defect is a sum over edges of 2 x_i x_j, so its minimum is always zero.
    check(all(abs(bad[bits] - sum(2 * weight for i, j, weight in edges
                                 if ((bits >> i) & 1) == 1 and ((bits >> j) & 1) == 1)) < 1e-12
              for bits in range(16)),
          "the defect counts the edges with both endpoints chosen, times two")

    check(abs(broken[(0, 0)] if (0, 0) in broken else 0.0) < 1e-12, "and it has no x0 term at all")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
