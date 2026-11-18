"""A noisy simulator: gate, then channel, then readout, then shots.

The simulator is deliberately thin. It has no transpiler, no noise model object
and no backend: a circuit is a list of (gate, wires, angle), each gate is
followed by the channel its error rate names, and the final state's diagonal is
what a measurement sees. That is enough to reproduce the chapter's device runs
and to show where the model stops working.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import channels, states
from .device import Rates, Readout, sigma_binomial

Op = Tuple[str, Tuple[int, ...], Optional[float]]


@dataclass
class Simulator:
    """Rates in, counts out. The channel is chosen once, for the whole run."""

    rates: Rates
    readout: Optional[Readout] = None
    channel: str = "depolarizing"
    seed: int = 11
    _rng: np.random.Generator = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.channel not in ("depolarizing", "amplitude", "phase", "none"):
            raise ValueError(f"unknown channel {self.channel!r}")
        # One generator for the whole simulator: seeding a fresh one per call
        # makes every setting of a CHSH run draw the same uniforms, and the
        # four correlators then share their noise instead of averaging it.
        self._rng = np.random.default_rng(self.seed)

    # -- the state path ---------------------------------------------------
    def state(self, n: int, ops: Sequence[Op], basis: Sequence[Op] = ()) -> np.ndarray:
        """The density matrix after the circuit, its channels, and the basis change."""
        if n < 1:
            raise ValueError(f"a circuit has at least one wire, got {n}")
        rho = states.zero(n)
        for gate, wires, theta in ops:
            rho = states.apply(rho, states._gate(gate, theta), wires, n)
            rho = self._noise(rho, gate, wires, n)
        for gate, wires, theta in basis:
            rho = states.apply(rho, states._gate(gate, theta), wires, n)
        return rho

    def _noise(self, rho: np.ndarray, gate: str, wires: Sequence[int], n: int) -> np.ndarray:
        if self.channel == "none":
            return rho
        try:
            rate = self.rates.error(gate, wires)
        except KeyError:
            return rho
        if rate <= 0:
            return rho
        if self.channel == "depolarizing":
            operators = channels.depolarizing(min(rate, 1.0), len(wires))
        elif self.channel == "amplitude":
            operators = channels.amplitude_damping(min(max(rate, 0.0), 1.0))
        else:
            operators = channels.phase_damping(min(max(rate, 0.0), 1.0))
        return channels.apply_channel(rho, operators, wires, n)

    # -- the measurement path ---------------------------------------------
    def distribution(self, n: int, ops: Sequence[Op], basis: Sequence[Op] = ()) -> np.ndarray:
        """Probabilities over basis states, before readout."""
        return states.probabilities(self.state(n, ops, basis))

    def run(
        self,
        n: int,
        ops: Sequence[Op],
        shots: int,
        basis: Sequence[Op] = (),
    ) -> Dict[str, int]:
        """Counts after readout, sampled with the simulator's rng."""
        if shots <= 0:
            raise ValueError(f"shots must be positive, got {shots}")
        probabilities = self.distribution(n, ops, basis)
        if self.readout is None:
            draws = self._rng.multinomial(shots, probabilities)
        else:
            draws = self.readout.sample(probabilities, shots, self._rng)
        keys = states.labels(n)
        return {key: int(count) for key, count in zip(keys, draws) if count}

    def peak(self, n: int, ops: Sequence[Op], index: int) -> float:
        """The ideal probability of one basis state, with no readout."""
        return float(self.distribution(n, ops)[index])

    def sigma(self, probability: float, shots: int) -> float:
        return sigma_binomial(probability, shots)


# -- the chapter's circuits ----------------------------------------------
def bell() -> List[Op]:
    """H on wire 0, CX(0,1): the state chapters 4 and 11 measured."""
    return [("h", (0,), None), ("cx", (0, 1), None)]


def chsh_setting(alpha: float, beta: float) -> Tuple[List[Op], List[Op]]:
    """A Bell pair measured in rotated bases: Ry(-2a) on A, Ry(-2b) on B.

    The angles are the ones chapter 4 used: (0, 45), (0, 135), (90, 45),
    (90, 135) degrees, which give the four correlators of a CHSH test.
    """
    ops = bell()
    # Chapter 4's convention: Ry(-angle) maps the axis at `angle` onto z, so
    # measuring after it gives E(a, b) = cos(a - b) on |Phi+>.
    basis = [
        ("ry", (0,), -np.deg2rad(alpha)),
        ("ry", (1,), -np.deg2rad(beta)),
    ]
    return ops, basis
