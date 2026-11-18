"""Exercise 2 (extend): a second channel, and the relation it breaks.

Run: python3 chapters/chapter12/files/exercises/ex2_damping.py

A depolarizing channel has one free number, and from a Bell pair's correlation
you can read its fidelity: F = (3E + 1) / 4. Amplitude damping breaks that
relation, so a report that infers a fidelity from a correlator is wrong by
tens of percent without saying so.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

import numpy as np

from noise import channels, states


def bell() -> np.ndarray:
    rho = states.zero(2)
    rho = states.apply(rho, states._gate("h"), (0,), 2)
    return states.apply(rho, states._gate("cx"), (0, 1), 2)


def correlation(rho: np.ndarray) -> float:
    p = states.probabilities(rho)
    return float(p[0] + p[3] - p[1] - p[2])


def fidelity(rho: np.ndarray) -> float:
    return states.fidelity_to(rho, 0)


def implied_fidelity_from_depolarising(correlator: float) -> float:
    """The F a depolarising model would infer from this correlator."""
    return (3 * correlator + 1) / 4


def gamma_for(t1_us: float, gate_us: float) -> float:
    """The damping probability of a gate that lasts gate_us."""
    if t1_us <= 0 or gate_us < 0:
        raise ValueError(f"times must be positive, got T1={t1_us}, t={gate_us}")
    return float(1 - np.exp(-gate_us / t1_us))


def table(gammas: List[float]) -> List[Dict[str, float]]:
    rows = []
    for gamma in gammas:
        rho = channels.apply_channel(bell(), channels.amplitude_damping(gamma), (0,), 2)
        correlator = correlation(rho)
        honest = fidelity(rho)
        rows.append(
            {
                "gamma": gamma,
                "correlation": correlator,
                "fidelity": honest,
                "implied": implied_fidelity_from_depolarising(correlator),
                "error": implied_fidelity_from_depolarising(correlator) - honest,
            }
        )
    return rows


def checks(check: Callable[[bool, str], None]) -> None:
    rows = table([0.01, 0.05, 0.2])
    check(len(rows) == 3, "three damping strengths")

    first = rows[0]
    check(abs(first["correlation"] - 0.99) < 1e-9, "at gamma 0.01 the correlation is 0.99")
    check(abs(first["fidelity"] - 0.5) < 1e-9, "and the fidelity is 0.5, because 00 is untouched")
    check(abs(first["implied"] - 0.9925) < 1e-9, "the depolarising relation infers 0.9925 from the correlation")
    check(first["error"] > 0.49, "which is wrong by half the state")

    check(abs(rows[1]["correlation"] - 0.95) < 1e-9, "at gamma 0.05 the correlation is 0.95")
    check(abs(rows[1]["fidelity"] - 0.5) < 1e-9, "the fidelity is still 0.5")
    check(abs(rows[2]["fidelity"] - 0.5) < 1e-9, "the fidelity never moves, because P(00) is never touched")
    check(abs(rows[2]["correlation"] - 0.8) < 1e-9, "at gamma 0.2 the correlation is 0.8")

    for row in rows:
        check(row["error"] > 0.0, f"the inferred fidelity is above the true one at gamma {row['gamma']}")
        check(row["correlation"] < 1.0, "and the correlation is below one everywhere")

    check(abs(gamma_for(100.0, 0.3) - 0.002996) < 1e-5, "a 0.3 microsecond gate on T1=100 is 0.0030")
    check(gamma_for(100.0, 1.0) > gamma_for(100.0, 0.3), "a longer gate damps more")
    check(abs(gamma_for(50.0, 0.3) - 0.005988) < 1e-5, "half the T1 doubles the damping")

    for bad in (0.0, -5.0):
        try:
            gamma_for(bad, 0.3)
        except ValueError:
            check(True, f"T1={bad} is refused")
        else:
            check(False, f"T1={bad} is refused")

    phase = channels.apply_channel(bell(), channels.phase_damping(0.05), (0,), 2)
    check(abs(correlation(phase) - 1.0) < 1e-12, "phase damping leaves the computational correlator at exactly 1.0")
    check(states.coherence(phase, 0, 3) < 0.5, "while the coherence falls, so the correlator is blind to it")
    check(abs(fidelity(phase) - 0.5) < 1e-9, "the fidelity is 0.5, as it was under amplitude damping")
    check(abs(states.probabilities(phase)[1]) < 1e-12, "and no population appears outside 00 and 11")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
