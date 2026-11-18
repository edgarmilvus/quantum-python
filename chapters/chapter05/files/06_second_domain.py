"""Demo 06: the same arithmetic on an A/B test, with no quantum mechanics.

Run: python3 chapters/chapter05/files/06_second_domain.py

Two versions of a page, two conversion counts, one interval each and one difference.
It is the same question as a correlation estimate: what did I measure, and how wrong
could it be?
"""

import math

import numpy as np

from stats import interval_width, wilson


def difference_interval(a_hits: int, a_total: int, b_hits: int, b_total: int, z: float = 1.96):
    p_a = a_hits / a_total
    p_b = b_hits / b_total
    difference = p_b - p_a
    error = math.sqrt(p_a * (1 - p_a) / a_total + p_b * (1 - p_b) / b_total)
    return difference, difference - z * error, difference + z * error


def main() -> None:
    rng = np.random.default_rng(8)
    # A converts at 4%, B at 5%, 20,000 visitors each.
    a_hits = int(rng.binomial(20_000, 0.04))
    b_hits = int(rng.binomial(20_000, 0.05))

    for name, hits, total in (("A", a_hits, 20_000), ("B", b_hits, 20_000)):
        low, high = wilson(hits, total)
        print(f"{name}: {hits}/{total} = {hits/total:.4f}  "
              f"95% [{low:.4f}, {high:.4f}]  width {interval_width(hits, total):.4f}")

    difference, low, high = difference_interval(a_hits, 20_000, b_hits, 20_000)
    print()
    print(f"difference B - A: {difference:+.4f}  95% [{low:+.4f}, {high:+.4f}]")
    print(f"crosses zero: {low < 0 < high}")
    print()
    print("the per-arm widths overlap, and the difference is still resolved")
    print("because the difference has its own, smaller, error")
    print()
    print("with 200 visitors per arm instead:")
    for scale in (100,):
        a_small = int(rng.binomial(scale * 2, 0.04))
        b_small = int(rng.binomial(scale * 2, 0.05))
        d, lo, hi = difference_interval(a_small, scale * 2, b_small, scale * 2)
        print(f"  difference {d:+.4f}  95% [{lo:+.4f}, {hi:+.4f}]  crosses zero: {lo < 0 < hi}")


if __name__ == "__main__":
    main()
