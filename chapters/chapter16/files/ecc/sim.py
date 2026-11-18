"""Simulation of the repetition code, and what it cannot protect.

Two channels. A bit-flip channel is the one the code is built for: independent X
errors, corrected by majority, with a logical error rate given by a binomial tail.
A phase-flip channel is the one it ignores: Z errors do not move a codeword in the
computational basis, so the vote sees nothing and the logical phase drifts.

The second channel is why a surface code exists: it checks both axes, which costs a
second dimension of qubits and buys a threshold.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np

from .code import Repetition, logical_error_ideal


def sample_bitflips(
    distance: int, p: float, trials: int, seed: int = 0
) -> Tuple[int, int]:
    """Monte Carlo: how many of `trials` codewords decode to the wrong bit."""
    if trials < 1:
        raise ValueError(f"trials must be positive, got {trials}")
    if not 0 <= p <= 1:
        raise ValueError(f"a probability is in [0, 1], got {p}")
    rng = np.random.default_rng(seed)
    code = Repetition(distance)
    wrong = 0
    for _ in range(trials):
        flips = rng.random(distance) < p
        bits = [int(flip) for flip in flips]  # prepared |0...0>, so a flip sets the bit
        if code.decode(bits) != 0:
            wrong += 1
    return wrong, trials


def phase_flip_error(distance: int, p: float) -> float:
    """The logical error on the axis the code does not check.

    A Z error leaves every codeword bit alone, so the vote cannot see it and the
    logical phase is the parity of the Z errors: (1 - (1 - 2p)^d) / 2.
    """
    if not 0 <= p <= 1:
        raise ValueError(f"a probability is in [0, 1], got {p}")
    if distance < 3:
        raise ValueError(f"a repetition code has distance at least three, got {distance}")
    return float((1 - (1 - 2 * p) ** distance) / 2)


def curve(distances: Sequence[int], p: float, points: int = 40) -> Dict[int, List[Tuple[float, float]]]:
    """The binomial logical error against the physical rate, one list per distance."""
    if points < 2:
        raise ValueError(f"a curve has at least two points, got {points}")
    out: Dict[int, List[Tuple[float, float]]] = {}
    for distance in distances:
        out[distance] = [
            (float(rate), logical_error_ideal(distance, float(rate)))
            for rate in np.linspace(0.0, 0.5, points)
        ]
    return out


def break_even(distance: int) -> float:
    """The physical rate at which the code stops helping: exactly one half.

    With a single error axis there is no threshold below the point where the noise
    is no longer a perturbation, which is the difference between this code and a
    surface code.
    """
    if distance < 3:
        raise ValueError(f"a repetition code has distance at least three, got {distance}")
    low, high = 0.0, 0.5
    for _ in range(60):
        middle = (low + high) / 2
        if logical_error_ideal(distance, middle) < middle:
            low = middle
        else:
            high = middle
    return float((low + high) / 2)


def device_table(record: dict) -> List[dict]:
    """Read a recorded run into rows of physical and logical rates."""
    rows = []
    for entry in record["results"]:
        distance = int(entry["distance"])
        prepared = int(entry["prepared"])
        code = Repetition(distance)
        total = sum(entry["counts"].values())
        flips = 0.0
        wrong = 0
        for key, count in entry["counts"].items():
            bits = [int(character) for character in str(key)[::-1]]
            flips += sum(1 for value in bits if value != prepared) * count
            if code.decode(bits) != prepared:
                wrong += count
        rows.append(
            {
                "distance": distance,
                "prepared": prepared,
                "idle_us": float(entry.get("idle_us", 0.0)),
                "layers": int(entry.get("layers", 0)),
                "physical": flips / (total * distance),
                "logical": wrong / total,
                "shots": total,
            }
        )
    return rows
