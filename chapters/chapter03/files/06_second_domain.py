"""Demo 06: the same answer from two plans, and what the plan costs.

Not quantum. A computation with a sequential plan and a wide plan produces the
same number, and the difference between them is the chapter's subject in a medium
where the reader can time both.

Run: python3 chapters/chapter03/files/06_second_domain.py
"""

import time

import numpy as np

SIZE = 200_000


def sequential(values):
    """One step per element: the depth is the length."""
    total = 0.0
    for value in values:
        total += value * value
    return total


def wide(values):
    """One step, applied to the whole array: the depth is one."""
    return float(np.sum(np.asarray(values) ** 2))


def main() -> None:
    values = np.linspace(0.0, 1.0, SIZE)

    start = time.perf_counter()
    loop_answer = sequential(values)
    loop_time = time.perf_counter() - start

    start = time.perf_counter()
    wide_answer = wide(values)
    wide_time = time.perf_counter() - start

    print(f"elements: {SIZE}")
    print(f"sequential: {loop_answer:.6f} in {loop_time * 1e3:.1f} ms, depth {SIZE}")
    print(f"wide:       {wide_answer:.6f} in {wide_time * 1e3:.3f} ms, depth 1")
    print(f"same answer: {abs(loop_answer - wide_answer) < 1e-6}")
    print(f"speed ratio: {loop_time / wide_time:.1f}x")
    print()
    print("same result, different plan, and the plan is what the time measures")
    print("a compiler does to a circuit what numpy does to a loop")


if __name__ == "__main__":
    main()
