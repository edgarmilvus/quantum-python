"""Exercise 5, file 3 of 3: the wiring.

Reads the idle-time run, summarises every row with the pure file, and renders the
one row where the code was working hardest.
"""

from __future__ import annotations

import json
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

from plan_core import summarise, verdict
from plan_render import render

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def load() -> dict:
    return json.loads((ROOT / "runs/chapter16/0029-idle-0-20-60us-4096-ibm/result.json").read_text())


def summarise_all() -> List[Dict[str, float]]:
    rows = []
    for entry in load()["results"]:
        summary = summarise(entry["distance"], entry["prepared"], entry["counts"])
        summary["distance"] = float(entry["distance"])
        summary["idle_us"] = float(entry["idle_us"])
        rows.append(summary)
    return rows


def hardest() -> Dict[str, float]:
    return max(summarise_all(), key=lambda row: row["physical"])


def report() -> str:
    summary = hardest()
    title = f"d={int(summary['distance'])} at {summary['idle_us']:.0f} us"
    return render(summary, title, verdict(summary))


def checks(check: Callable[[bool, str], None]) -> None:
    rows = summarise_all()
    check(len(rows) == 12, "twelve rows from the record")
    check(all(row["shots"] == 4096 for row in rows), "every row has 4,096 shots")

    text = report()
    check("d=5 at 60 us" in text, "the hardest row is d=5 at sixty microseconds")
    check("verdict" in text, "the table ends on a verdict")
    check("nan" not in text.lower(), "no number failed to compute")

    worst = hardest()
    check(abs(worst["physical"] - 0.2829) < 0.01, "its physical rate is 0.283")
    check(abs(worst["logical"] - 0.1387) < 0.01, "its logical rate is 0.139")
    check(0 <= worst["low"] <= worst["logical"] <= worst["high"] <= 1, "the interval brackets the rate")

    best = min(rows, key=lambda row: row["physical"])
    check(best["physical"] < 0.02, "the quietest row is under two percent")
    check(verdict(best) in ("ten times better", "better than the physical rate"), "and the code improves it")

    zero_rows = [row for row in rows if row["logical"] == 0.0]
    check(len(zero_rows) == 4, "four rows saw no logical error at all")
    check(all(row["high"] < 0.002 for row in zero_rows), "and each carries an upper bound below 0.002")

    check(report() == text, "the report is deterministic")

    for bad in ((2, 0, {"00": 1}), (3, 2, {"000": 1}), (3, 0, {})):
        try:
            summarise(*bad)
        except ValueError:
            check(True, f"{bad} is refused")
        else:
            check(False, f"{bad} is refused")

    check(verdict({"physical": 0.1, "logical": 0.2}) == "no better than the physical rate",
          "a code that loses is called a loser")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
