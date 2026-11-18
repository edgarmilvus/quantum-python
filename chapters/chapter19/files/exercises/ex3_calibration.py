"""Exercise 3 (measure): the calibration is most of the job.

Run: python3 chapters/chapter19/files/exercises/ex3_calibration.py

The pipeline runs the task once and the calibration n+1 times, so the overhead is
(n+1)/(n+2): 83% at four qubits, 90% at eight, and 95% at twenty. The calibration is
per qubit, and the task is not, so the overhead grows with the machine — which is the
opposite of what a reader expects from "more qubits".
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

from pipe import estimate, spec


def overhead(qubits: int) -> float:
    """The share of the circuits that exist only to calibrate."""
    if qubits < 2:
        raise ValueError(f"a task has at least two qubits, got {qubits}")
    return (qubits + 1) / (qubits + 2)


def table(qubits: List[int]) -> List[Dict[str, float]]:
    return [{"qubits": float(q), "overhead": overhead(q), "circuits": float(q + 2)} for q in qubits]


def checks(check: Callable[[bool, str], None]) -> None:
    rows = {int(row["qubits"]): row for row in table([4, 8, 20, 50])}

    check(abs(rows[4]["overhead"] - 5 / 6) < 1e-12, "at four qubits the overhead is five sixths")
    check(abs(rows[8]["overhead"] - 9 / 10) < 1e-12, "at eight it is nine tenths")
    check(rows[20]["overhead"] > rows[8]["overhead"], "and it grows with the machine")
    check(rows[50]["overhead"] > 0.98, "at fifty qubits it is almost the whole job")

    check(rows[4]["circuits"] == 6, "four qubits are six circuits")
    check(rows[8]["circuits"] == 10, "eight are ten")

    task = spec.Task(name="bv-1011", qubits=4, shots=2048, provider="ibm")
    check(task.circuits == 6, "the task object agrees")

    wide = spec.Task(name="bv-wide", qubits=8, shots=2048, provider="ibm", secret="10110110")
    check(wide.circuits == 10, "an eight-qubit task needs ten circuits")
    check(overhead(8) > overhead(4), "and a larger share of them is calibration")

    freed = estimate.price("local", 6, 2048) - estimate.price("local", 1, 2048)
    check(freed == 0.0, "on a free provider the overhead costs nothing")

    ionq = estimate.price("ionq", 6, 2048) - estimate.price("ionq", 1, 2048)
    check(abs(ionq - 820.7) < 1.0, "on IonQ the five calibration circuits cost 820.70")

    for bad in (1, 0, -3):
        try:
            overhead(bad)
        except ValueError:
            check(True, f"{bad} qubits is refused")
        else:
            check(False, f"{bad} qubits is refused")

    check(all(0 < row["overhead"] < 1 for row in rows.values()), "every overhead is a fraction")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
