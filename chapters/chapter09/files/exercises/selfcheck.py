"""Run one exercise's checks on its own.

Loaded by the `if __name__ == "__main__"` block at the bottom of each exercise,
so `python3 ex3_shots.py` prints that exercise's total and nothing else.
"""

from __future__ import annotations

import sys
from types import ModuleType


def main(module: ModuleType) -> None:
    count = 0
    failures: list[str] = []

    def check(condition: bool, description: str) -> None:
        nonlocal count
        count += 1
        if not condition:
            failures.append(description)

    module.checks(check)

    print()
    if failures:
        print(f"{len(failures)} failed:")
        for failure in failures:
            print(f"  - {failure}")
        raise SystemExit(1)
    print(f"{count}/{count} checks passed")
