"""Exercise 3 (measure): the syndrome's own error rate is the whole budget.

Run: python3 chapters/chapter17/files/exercises/ex3_budget.py

A code corrects an error it can see. If the syndrome is wrong more often than the
data, the correction adds errors of its own, and the arithmetic is merciless: on
this device a clean codeword produces a false syndrome 6.3% of the time while a data
qubit errs at about 3.4%, so the diagnosis is worse than the disease.
"""

import json
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def rates() -> Dict[str, float]:
    syndrome = json.loads((ROOT / "runs/chapter17/0034-syndrome-two-registers-8192-ibm/result.json").read_text())
    memory = json.loads((ROOT / "runs/chapter17/0031-dynamic-correction-4096-ibm/result.json").read_text())
    row = next(entry for entry in syndrome["results"] if entry["prepared"] == 1)
    total = sum(row["syndromes"].values())
    false_syndrome = sum(count for key, count in row["syndromes"].items() if key != "00") / total

    by = {(entry["prepared"], entry["idle_us"], entry["corrected"]): entry for entry in memory["results"]}
    data = by[(1, 0.0, False)]
    data_total = sum(data["counts"].values())
    physical = sum(
        sum(1 for character in key if int(character) != 1) * count
        for key, count in data["counts"].items()
    ) / (data_total * 3)
    return {"false syndrome": false_syndrome, "physical": physical, "shots": float(total)}


def ratio(r: Dict[str, float]) -> float:
    return r["false syndrome"] / r["physical"]


def checks(check: Callable[[bool, str], None]) -> None:
    r = rates()
    check(abs(r["false syndrome"] - 0.063) < 0.01, "the false syndrome rate is 6.3%")
    check(abs(r["physical"] - 0.019) < 0.01, "the data error is about 1.9%")
    check(r["false syndrome"] > r["physical"], "so the syndrome is dirtier than the data")
    check(abs(ratio(r) - 3.3) < 0.4, "by a factor of about 3.3")

    check(r["shots"] == 8192, "the syndrome run used 8,192 shots")

    # A code pays when the diagnosis is at least as good as the thing diagnosed.
    check(ratio(r) > 1.0, "and this one does not")

    threshold = 0.019 / 2
    check(threshold < r["false syndrome"], "a syndrome below half the data error would be comfortable")

    # The consequence, measured: correction on a clean codeword is worse than none.
    memory = json.loads((ROOT / "runs/chapter17/0031-dynamic-correction-4096-ibm/result.json").read_text())
    by = {(entry["prepared"], entry["idle_us"], entry["corrected"]): entry for entry in memory["results"]}

    def logical(entry) -> float:
        total = sum(entry["counts"].values())
        wrong = 0
        for key, count in entry["counts"].items():
            bits = [int(character) for character in key[::-1]]
            if (sum(bits) * 2 > 3) != entry["prepared"]:
                wrong += count
        return wrong / total

    check(logical(by[(1, 0.0, True)]) > 10 * logical(by[(1, 0.0, False)]),
          "and the corrected circuit is an order of magnitude worse than the control")
    check(logical(by[(0, 0.0, True)]) < 0.005, "on the zero codeword the damage is smaller, because the readout asymmetry favours it")

    check(0 < threshold < 1, "the threshold is a probability")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
