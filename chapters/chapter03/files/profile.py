"""What a recorded backend profile predicts, before anything runs.

The profile is a JSON file captured from a real device: basis gates, a handful of
two-qubit error rates, one readout error. The model here is deliberately crude, and
the chapter compares its prediction with the measured Bell run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "profiles" / "ibm_fez.json"


def load(path: Path = DEFAULT_PATH) -> dict:
    data = json.loads(Path(path).read_text())
    if "basis_gates" not in data or "cz_errors" not in data:
        raise ValueError(f"{path} is not a backend profile: missing basis_gates or cz_errors")
    return data


def two_qubit_errors(profile: dict) -> List[float]:
    return [entry["cz_error"] for entry in profile["cz_errors"] if "cz_error" in entry]


def worst_two_qubit_error(profile: dict) -> float:
    errors = two_qubit_errors(profile)
    if not errors:
        raise ValueError("the profile has no two-qubit error rates")
    return max(errors)


def predicted_error(
    profile: dict,
    two_qubit_gates: int,
    measured_qubits: int,
    two_qubit_error: float | None = None,
) -> float:
    """A first-order estimate: independent errors compose multiplicatively.

    1 - (1 - e_two)^gates * (1 - e_readout)^qubits

    First order is enough for a chapter that compares orders of magnitude; the
    measured run is the authority, and the text says so.
    """
    if two_qubit_gates < 0 or measured_qubits < 0:
        raise ValueError("gate and qubit counts cannot be negative")
    e_two = worst_two_qubit_error(profile) if two_qubit_error is None else two_qubit_error
    e_readout = float(profile.get("readout_error_q0", 0.0))
    survival = (1.0 - e_two) ** two_qubit_gates * (1.0 - e_readout) ** measured_qubits
    return 1.0 - survival


def depth_where_prediction_crosses(profile: dict, threshold: float, two_qubit_per_layer: int = 1) -> int:
    """The first depth whose predicted error exceeds `threshold`."""
    if not 0.0 < threshold < 1.0:
        raise ValueError(f"threshold must be inside (0, 1), got {threshold}")
    for depth in range(1, 100_000):
        if predicted_error(profile, depth * two_qubit_per_layer, 2) > threshold:
            return depth
    raise ValueError("threshold never reached")


def summary(profile: dict) -> Dict[str, object]:
    return {
        "backend": profile.get("backend"),
        "qubits": profile.get("num_qubits"),
        "basis": profile.get("basis_gates"),
        "two_qubit_errors": two_qubit_errors(profile),
        "readout": profile.get("readout_error_q0"),
        "t1_us": None if profile.get("t1_q0") is None else round(profile["t1_q0"] * 1e6, 1),
        "t2_us": None if profile.get("t2_q0") is None else round(profile["t2_q0"] * 1e6, 1),
    }
