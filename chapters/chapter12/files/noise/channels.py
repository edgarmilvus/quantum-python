"""The three channels a device applies, as Kraus operators.

A channel is a list of operators K_i with sum K_i-dagger K_i = 1; it maps a state
to sum K_i rho K_i-dagger. The three in this file are the ones a superconducting
device produces: depolarizing when a gate misses, amplitude damping when the
qubit relaxes toward |0>, phase damping when it forgets its phase and keeps its
population.

The convention that matters: `depolarizing(p)` replaces the state with the
maximally mixed one with probability p, so a Bell pair's correlation decays as
exactly (1-p) per gate. That is the number the survival arithmetic multiplies.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np

from .states import Matrix, full, paulis

Kraus = List[Matrix]


def _identity(n: int) -> Matrix:
    return np.eye(2 ** n, dtype=complex)


def depolarizing(p: float, wires: int = 1) -> Kraus:
    """Replace the state with I/d with probability p.

    With probability 1-p the state is untouched. The remaining p is spread over
    the 4^n - 1 non-identity Pauli strings, which is what makes the channel
    isotropic: every Pauli error is equally likely.
    """
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"a probability is in [0, 1], got {p}")
    dimension = 2 ** wires
    strings = paulis(wires)
    survive = 1.0 - p + p / dimension ** 2
    spread = p / dimension ** 2
    if survive < 0:
        raise ValueError(f"p={p} is too large for a channel on {wires} wires")
    operators: Kraus = [np.sqrt(survive) * _identity(wires)]
    operators += [np.sqrt(spread) * matrix for _, matrix in strings[1:]]
    return operators


def amplitude_damping(gamma: float) -> Kraus:
    """|1> decays to |0> with probability gamma: the T1 channel."""
    if not 0.0 <= gamma <= 1.0:
        raise ValueError(f"gamma is in [0, 1], got {gamma}")
    k0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    k1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    return [k0, k1]


def phase_damping(lam: float) -> Kraus:
    """Coherence decays by (1-lam), the population is untouched: the T2 channel."""
    if not 0.0 <= lam <= 1.0:
        raise ValueError(f"lambda is in [0, 1], got {lam}")
    k0 = np.array([[1, 0], [0, np.sqrt(1 - lam)]], dtype=complex)
    k1 = np.array([[0, 0], [0, np.sqrt(lam)]], dtype=complex)
    return [k0, k1]


def apply_channel(rho: Matrix, operators: Kraus, wires: Sequence[int], n: int) -> Matrix:
    """sum K_i rho K_i-dagger, with each K lifted to the whole register."""
    out = np.zeros_like(rho)
    for operator in operators:
        lifted = full(operator, wires, n)
        out += lifted @ rho @ lifted.conj().T
    return out


def check_complete(operators: Kraus) -> float:
    """||sum K-dagger K - 1||, which must be zero for a valid channel."""
    total = np.zeros_like(operators[0], dtype=complex)
    for operator in operators:
        total += operator.conj().T @ operator
    return float(np.linalg.norm(total - np.eye(total.shape[0])))


def channel_report(operators: Kraus) -> Tuple[int, float]:
    """How many Kraus operators, and how far from complete."""
    return len(operators), check_complete(operators)


def relaxation_channels(t1_us: float, t2_us: float, gate_us: float) -> Tuple[Kraus, Kraus]:
    """Amplitude and phase damping for a gate that lasts `gate_us`.

    For a gate much shorter than T1 the decay is exponential:
    gamma = 1 - exp(-t/T1) and lambda = 1 - exp(-t/T2). The two are not
    independent: T2 <= 2 T1 always, so the pure dephasing rate is what is left
    after the energy relaxation is subtracted.
    """
    if t1_us <= 0 or t2_us <= 0 or gate_us < 0:
        raise ValueError(f"times must be positive, got T1={t1_us}, T2={t2_us}, t={gate_us}")
    if t2_us > 2 * t1_us + 1e-9:
        raise ValueError(f"T2={t2_us} exceeds 2 T1={2 * t1_us}, which is impossible")
    gamma = 1 - np.exp(-gate_us / t1_us)
    lam = 1 - np.exp(-gate_us / t2_us)
    # A T2 decay of exp(-t/T2) contains the energy decay exp(-t/2T1); what is
    # left is pure dephasing, which is what the phase channel models.
    pure = 1 - np.exp(-gate_us * (1 / t2_us - 1 / (2 * t1_us)))
    return amplitude_damping(float(gamma)), phase_damping(float(min(1.0, max(0.0, pure))))
