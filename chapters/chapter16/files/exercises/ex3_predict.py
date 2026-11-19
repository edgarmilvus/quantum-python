"""Exercise 3 (measure): predict the device from its own physical error.

Run: python3 chapters/chapter16/files/exercises/ex3_predict.py

The binomial law takes the measured physical rate of a device run and predicts the
logical rate. On the twelve rows of the idle experiment the prediction is within a
tenth of the measurement, which is the strongest evidence in the chapter that the
device's qubit errors are close to independent.
"""

import json
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

from ecc import code, sim

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def rows() -> List[Dict[str, float]]:
    record = json.loads((ROOT / "runs/chapter16/0029-idle-0-20-60us-4096-ibm/result.json").read_text())
    out = []
    for row in sim.device_table(record):
        row["predicted"] = code.logical_error_ideal(row["distance"], row["physical"])
        row["error"] = abs(row["logical"] - row["predicted"])
        out.append(row)
    return out


def worst(rows_: List[Dict[str, float]]) -> Dict[str, float]:
    return max(rows_, key=lambda row: row["error"])


def where_it_stops() -> float:
    """The physical rate at which the d=3 code stops helping."""
    return sim.break_even(3)


def checks(check: Callable[[bool, str], None]) -> None:
    data = rows()
    check(len(data) == 12, "twelve rows from the record")
    check(all(row["predicted"] >= 0 for row in data), "every prediction is a probability")

    high = [row for row in data if row["physical"] > 0.1]
    check(len(high) == 4, "four rows sit above a ten percent physical rate")
    check(all(row["error"] < 0.01 for row in high), "and all four are predicted within a point")

    low = [row for row in data if row["physical"] < 0.03]
    check(all(abs(row["logical"] - row["predicted"]) < 0.002 for row in low),
          "the quiet rows are predicted within two tenths of a point")

    worst_row = worst(data)
    check(worst_row["error"] < 0.01, "no row misses by more than one point")
    check(abs(worst_row["physical"] - 0.2564) < 0.01 or abs(worst_row["physical"] - 0.2829) < 0.01,
          "the largest miss is one of the two sixty-microsecond rows")

    huge = [row for row in data if row["physical"] > 0.25]
    check(len(huge) == 2, "two rows lose a quarter of their qubits")
    check(all(row["logical"] < row["physical"] for row in huge),
          "and the code still beats the physical rate there")

    check(abs(where_it_stops() - 0.5) < 1e-6, "the code stops helping at one half")

    d3 = next(row for row in data if row["distance"] == 3 and row["prepared"] == 1 and 0.05 < row["physical"] < 0.2)
    d5 = next(row for row in data if row["distance"] == 5 and row["prepared"] == 1 and 0.05 < row["physical"] < 0.2)
    check(d3["logical"] / d5["logical"] > 2, "the distance buys more than a factor of two at twenty microseconds")

    for row in data:
        check(0 <= row["logical"] <= 1, "every measured rate is a fraction")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
