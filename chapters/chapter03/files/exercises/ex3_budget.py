"""Exercise 3 (measure): how much of the error is readout, and how much is gates.

A single number, 5.4% of shots landing on the wrong Bell state, can be blamed on the
device in general. The profile splits it: readout happens once per measured qubit,
and the circuit's two-qubit gates happen once per gate.

Run: python3 chapters/chapter03/files/exercises/ex3_budget.py
"""

import pathlib as _pathlib
import json
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from profile import load, predicted_error, worst_two_qubit_error

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def budget(device: dict, two_qubit_gates: int, measured_qubits: int) -> Dict[str, float]:
    """Split the predicted error into its readout and gate parts, first order."""
    e_two = worst_two_qubit_error(device)
    e_read = float(device["readout_error_q0"])
    gate = two_qubit_gates * e_two
    readout = measured_qubits * e_read
    return {
        "gate": gate,
        "readout": readout,
        "total_first_order": gate + readout,
        "total_exact": predicted_error(device, two_qubit_gates, measured_qubits),
    }


def observed() -> float:
    run = json.loads((ROOT / "runs/0001-ibm-fez-bell/result.json").read_text())
    return float(run["derived"]["p_anti_correlated"])


def checks(check: Callable[[bool, str], None]) -> None:
    device = load()
    parts = budget(device, two_qubit_gates=1, measured_qubits=2)

    check(abs(parts["gate"] - 0.009599078697140023) < 1e-12, "one worst-case CZ costs 0.0096")
    check(abs(parts["readout"] - 2 * 0.029296875) < 1e-12, "two readouts cost 0.0586 first order")
    check(parts["readout"] > parts["gate"], "readout dominates this circuit")
    check(abs(parts["total_exact"] - 0.0668) < 5e-4, "the exact composition predicts 6.7%")
    check(parts["total_exact"] < parts["total_first_order"], "the exact total is below the sum of parts")

    seen = observed()
    check(abs(seen - 0.0537) < 1e-4, "the recorded run shows 5.4%")
    check(abs(seen - parts["total_exact"]) < 0.02, "the prediction is within two points of the run")
    check(seen < parts["readout"], "the observed error is below the first-order readout estimate")

    check(budget(device, 0, 0)["total_exact"] == 0.0, "no gates and no readout predict nothing")
    check(budget(device, 10, 2)["total_exact"] > budget(device, 1, 2)["total_exact"], "more gates predict more error")

    try:
        budget(device, -1, 2)
    except ValueError:
        check(True, "a negative gate count is refused")
    else:
        check(False, "a negative gate count is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
