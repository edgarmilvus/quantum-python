"""Exercise 3 (measure): what the two classical bits are worth.

Run: python3 chapters/chapter20/files/exercises/ex3_correction.py

The device ran the same tomography three times. The difference between the corrected and
the uncorrected fidelity is the value of the two bits, and the difference between the
dynamic and the postselected runs is the value of doing the correction on the machine.
"""

import json
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from teleport import Calibration, run

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def record() -> dict:
    path = ROOT / "runs/chapter20/0042-teleport-pi3-pi4-2048-ibm/result.json"
    if not path.exists():
        raise FileNotFoundError(f"no record at {path}")
    return json.loads(path.read_text())


def correction_rate(counts: Dict[str, int]) -> Dict[str, float]:
    """How often each correction fires: X on m1, Z on m0."""
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no rate")
    ones = lambda index: sum(n for key, n in counts.items() if key[len(key) - 1 - index] == "1")
    return {"x": ones(1) / total, "z": ones(0) / total}


def checks(check: Callable[[bool, str], None]) -> None:
    data = record()
    dynamic = run(data, "dynamic")
    post = run(data, "postselect")
    control = run(data, "uncorrected")

    check(abs(dynamic.fidelity - 0.9558) < 0.005, "the dynamic run is at 0.9558")
    check(abs(post.fidelity - 0.9499) < 0.005, "the postselect run at 0.9499")
    check(abs(control.fidelity - 0.4858) < 0.01, "the control at 0.4858")
    check(abs((dynamic.fidelity - control.fidelity) - 0.470) < 0.01, "the bits are worth 0.470")
    check(abs(dynamic.fidelity - post.fidelity) < 0.02, "the two corrections agree within two points")
    check(control.fidelity < 0.55, "and the control is not a teleportation")

    rate = correction_rate(data["dynamic"]["counts"]["Z"])
    check(0.4 < rate["x"] < 0.6, "the X correction fires about half the time")
    check(0.4 < rate["z"] < 0.6, "and so does the Z correction")
    check(abs(rate["x"] + rate["z"] - 1.0) < 0.15, "the two outcomes are a fair pair")

    calibration = Calibration.from_counts(data["calibration"])
    check(calibration.p_zero_given_one > calibration.p_one_given_zero, "misreading a one is the common error")
    check(calibration.p_zero_given_one < 0.05, "and it is under five percent")

    check(len(data["calibration"]) == 4, "four calibration circuits")
    check(sum(len(data[kind]["counts"]) for kind in ("dynamic", "postselect", "uncorrected")) == 9,
          "nine tomography circuits")
    check(data["shots"] == 2048, "at 2,048 shots each")

    error = 0.0
    try:
        correction_rate({})
    except ValueError:
        error = 1.0
    check(error == 1.0, "an empty histogram is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
