"""Exercise 4 (break): the pipeline without its guard.

Run: python3 chapters/chapter19/files/exercises/ex4_guard.py

The estimate is the only thing between a one-line task and a 985-dollar invoice. This
exercise prices the task without the guard, shows the ratio, and then shows what the
guard does: it refuses before a job exists, with the number in the message.

The defect is not a bug in the arithmetic; it is a pipeline with the arithmetic removed.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from pipe import estimate, spec


def invoice(task: spec.Task) -> Dict[str, float]:
    """What a pipeline without a budget guard would spend."""
    return {
        "circuits": float(task.circuits),
        "shots": float(task.shots),
        "usd": estimate.price(task.provider, task.circuits, task.shots),
    }


def checks(check: Callable[[bool, str], None]) -> None:
    task = spec.Task(name="bv-1011", qubits=4, shots=2048, provider="ibm", budget_usd=5.0)
    ionq = spec.Task(**{**task.__dict__, "provider": "ionq"})

    cheap = invoice(task)
    check(cheap["usd"] == 0.0, "the IBM invoice is zero")
    check(estimate.estimate(task).allowed, "and the guard allows it")

    expensive = invoice(ionq)
    check(abs(expensive["usd"] - 984.84) < 1.0, "the IonQ invoice is 984.84")
    check(expensive["usd"] > 190 * task.budget_usd, "which is 197 times the budget")
    check(expensive["circuits"] == 6.0, "for the same six circuits")

    refused = estimate.estimate(ionq)
    check(not refused.allowed, "the guard refuses the same task")
    check("984.84" in refused.reason, "and the message carries the number")
    check("5.00" in refused.reason, "and the budget")

    bigger = spec.Task(**{**ionq.__dict__, "budget_usd": 1000.0})
    check(estimate.estimate(bigger).allowed, "raising the budget to a thousand allows it")

    check(estimate.estimate(task, key_present=False).allowed is False, "and a missing key refuses as well")

    scaled = spec.Task(**{**ionq.__dict__, "shots": 4096})
    check(estimate.price("ionq", scaled.circuits, scaled.shots) > 1900, "doubling the shots doubles the invoice")

    check(estimate.cheapest(ionq) == "local", "the cheapest provider is not the one the task names")
    check(estimate.price("local", 6, 2048) == 0.0, "because the local run is free")

    for bad in (0, -1):
        try:
            estimate.price("ionq", bad, 2048)
        except ValueError:
            check(True, f"{bad} circuits is refused")
        else:
            check(False, f"{bad} circuits is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
