"""Exercise 5, file 3 of 3: the wiring.

Reads the GHZ records through the chapter's sources, asks the core for a ranking,
and renders it.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

from bench import sources, task

from plan_core import ranking, summarise, verdict
from plan_render import render


def rows() -> List[task.Row]:
    return sources.ibm_ghz() + [sources.qbraid_ghz(), sources.local_ghz()]


def report() -> str:
    data = rows()
    summary = summarise(data)
    return render(summary, ranking(data), "GHZ-3 at 4,096 shots", verdict(summary))


def checks(check: Callable[[bool, str], None]) -> None:
    text = report()
    check("GHZ-3 at 4,096 shots" in text, "the title names the task")
    check("ranking:" in text, "the report has a ranking")
    check("nan" not in text.lower(), "no number failed to compute")

    summary = summarise(rows())
    check(summary["rows"] == 4, "four sources")
    check(summary["device_rows"] == 2, "two of them device rows")
    check(summary["sim_rows"] == 2, "and two simulators")
    check(abs(summary["best"]) < 1e-9, "the best distance is zero")
    check(abs(summary["worst"] - 0.1616) < 0.005, "the worst is the delayed device row")
    check(summary["spread"] > 0.1, "the spread is more than a tenth")

    order = ranking(rows())
    check(order[0] == "qbraid, IonQ simulator", "the exact source ranks first")
    check(order[-1].startswith("ibm_kingston, 20"), "and the delayed device last")

    check(verdict(summary) == "an exact source wins and the devices are the story",
          "the verdict says an exact source wins")
    check(report() == text, "the report is deterministic")

    try:
        summarise([])
    except ValueError:
        check(True, "an empty ranking is refused")
    else:
        check(False, "an empty ranking is refused")

    try:
        summarise([rows()[0]])
    except ValueError:
        check(True, "a single row is refused")
    else:
        check(False, "a single row is refused")

    simulator_only = summarise([rows()[2], rows()[3]])
    check(verdict(simulator_only) == "simulators only: nothing here measures a machine",
          "and a table with no device says so")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
