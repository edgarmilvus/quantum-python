"""Exercise 2 (extend): a heavy edge moves the optimum and the angles.

Run: python3 chapters/chapter13/files/exercises/ex2_weights.py

The square from the chapter with edge 1-2 given weight three. The optimum rises
from 4 to 6, the best angles move, and the chapter's own p=1 angles, trained on
the unweighted instance, score 4.5769 when they meet the weighted objective
instead of the 4.7602 the weighted angles reach.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from qaoa import graph as g, qaoa, optimize


def ratio_under(graph: g.Graph, betas, gammas, optimum: float) -> float:
    """What a set of angles is worth on a given objective."""
    if optimum <= 0:
        raise ValueError(f"an optimum is positive, got {optimum}")
    mean = qaoa.expected_cut(graph, qaoa.state_for(graph, betas, gammas))
    return qaoa.approximation_ratio(mean, optimum)


def cut_table(graph: g.Graph) -> Dict[int, float]:
    return graph.all_cuts()


def checks(check: Callable[[bool, str], None]) -> None:
    weighted = g.weighted_square()
    plain = g.square_with_diagonal()

    optimum, best_bits = weighted.max_cut()
    check(optimum == 6.0, "the weighted optimum is 6, not 4")
    check(weighted.uniform_mean() == 3.0, "a uniform guess averages 3 on the weighted instance")
    check(weighted.spectrum() == {0.0: 2, 2.0: 6, 4.0: 6, 6.0: 2}, "the spectrum is 2/6/6/2")
    check(weighted.cut(0b0101) == 6.0, "0101 still reaches the optimum")
    check(plain.cut(0b0101) == 4.0, "and it was worth 4 before the weight")
    check(weighted.cut(0b1010) == 6.0, "the complement too")

    heavy = optimize.optimise(weighted, 1)
    check(abs(heavy.cost - 4.7602) < 1e-2, "the weighted p=1 optimum is 4.7602")
    check(abs(heavy.cost / 6.0 - 0.7934) < 1e-2, "which is 0.7934 of the weighted optimum")
    check(abs(heavy.betas[0] - 0.3927) < 1e-2, "at beta 0.3927")
    check(abs(heavy.gammas[0] - 0.4680) < 1e-2, "and gamma 0.4680")

    plain_angles = 0.3109, 0.5713
    check(abs(ratio_under(weighted, [plain_angles[0]], [plain_angles[1]], 6.0) - 0.7628) < 1e-2,
          "the unweighted angles score 0.7628 on the weighted objective")
    check(ratio_under(weighted, [plain_angles[0]], [plain_angles[1]], 6.0) < heavy.cost / 6.0,
          "so the weights are worth three points of ratio")
    check(ratio_under(plain, [heavy.betas[0]], [heavy.gammas[0]], 4.0) < heavy.cost / 6.0 + 0.2,
          "and the weighted angles are not the plain ones either")

    check(len(cut_table(weighted)) == 16, "the weighted instance still has sixteen assignments")

    for bad in (0.0, -2.0):
        try:
            g.Graph(n=3, edges=((0, 1, bad),))
        except ValueError:
            check(True, f"a weight of {bad} is refused")
        else:
            check(False, f"a weight of {bad} is refused")

    check(abs(sum(weight for _, _, weight in weighted.edges) - 6.0) < 1e-9,
          "the weights sum to six, which is the trivial upper bound on the cut")
    check(weighted.max_cut()[0] == sum(weight for _, _, weight in weighted.edges),
          "and in this instance the optimum reaches the bound")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
