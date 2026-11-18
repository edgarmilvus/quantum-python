"""Exercise 5, file 1 of 3: the pure part of the teleportation memo.

A recorded run in, the numbers a report owes out. No file, no printing, no clock.
"""

from __future__ import annotations

from typing import Dict

from teleport import Calibration, Prepared, run

KINDS = ("dynamic", "postselect", "uncorrected")


def summarise(record: Dict) -> Dict:
    if "prepared" not in record:
        raise ValueError("a record needs the prepared state")
    prepared = Prepared(record["prepared"]["theta"], record["prepared"]["phi"])
    calibration = Calibration.from_counts(record.get("calibration") or [])
    scores = {kind: run(record, kind) for kind in KINDS}
    best = max(scores, key=lambda kind: scores[kind].fidelity)
    gap = scores["dynamic"].fidelity - scores["uncorrected"].fidelity
    return {
        "theta": prepared.theta,
        "phi": prepared.phi,
        "readout": (calibration.p_one_given_zero, calibration.p_zero_given_one),
        "fidelity": {kind: scores[kind].fidelity for kind in KINDS},
        "best": best,
        "gap": gap,
        "shots": int(record["shots"]),
        "headline": (
            f"{best} teleports at {scores[best].fidelity:.4f}, "
            f"the correction is worth {gap:.4f}"
        ),
    }


def verdict(summary: Dict) -> str:
    """One sentence, because the result is a sentence and not a table."""
    if summary["fidelity"]["dynamic"] >= 0.90 and summary["gap"] >= 0.30:
        return "the state arrived, and the two classical bits carried it"
    if summary["fidelity"]["dynamic"] >= 2 / 3:
        return "the state arrived degraded, above the classical guess"
    return "the state did not arrive"
