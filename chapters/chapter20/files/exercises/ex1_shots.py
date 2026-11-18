"""Exercise 1 (repair): the shot count that ignores the multiplier.

Run: python3 chapters/chapter20/files/exercises/ex1_shots.py

The index records a job as `2048 x 6`: six circuits, each at 2,048 shots. A parser that
takes the first integer reports 2,048 shots for a job that took 12,288, and the book's
sample size then depends on how many circuits each run happened to have. The defect is one
missing multiplication.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import re
from typing import Callable


def shots_defective(cell: str) -> int:
    """The defect: the first integer in the cell, and nothing else."""
    match = re.search(r"(\d[\d,]*)", cell)
    return int(match.group(1).replace(",", "")) if match else 0


def shots(cell: str) -> int:
    """The repair: a multiplier is a multiplication, and a k is a thousand."""
    many = re.search(r"(\d[\d,]*)\s*x\s*(\d+)", cell)
    if many:
        return int(many.group(1).replace(",", "")) * int(many.group(2))
    thousands = re.search(r"(\d+)\s*k\b", cell, re.IGNORECASE)
    if thousands:
        return int(thousands.group(1)) * 1000
    one = re.search(r"(\d[\d,]*)", cell)
    return int(one.group(1).replace(",", "")) if one else 0


def checks(check: Callable[[bool, str], None]) -> None:
    check(shots("2048 x 6") == 12288, "six circuits at 2,048 shots are 12,288")
    check(shots_defective("2048 x 6") == 2048, "the defect reports one circuit's shots")

    check(shots("1024 x 36") == 36864, "thirty-six circuits multiply the same way")
    check(shots_defective("1024 x 36") == 1024, "and the defect does not")

    check(shots("200k (model)") == 200000, "200k is two hundred thousand")
    check(shots_defective("200k (model)") == 200, "the defect reads 200")

    check(shots("4096 (model)") == 4096, "a parenthetical does not change the count")
    check(shots("--") == 0, "a saved snapshot has no shots")
    check(shots("1024 (reused)") == 1024, "a reused count is still a count")

    check(shots("2048 x 6") > shots_defective("2048 x 6"), "the repair is larger on a multiplied row")
    check(shots("1024 x 36") > 30 * shots("1024"), "and by the multiplier, not by a constant")

    row = "4096 x 12"
    check(shots(row) == 49152, "four thousand and ninety-six times twelve")
    check(shots_defective(row) * 10 < shots(row), "the defect is off by an order of magnitude")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
