"""Demo 06: the same contract on a classical object.

A weighted coin has two outcomes and a normalization rule. It is not quantum,
and the point of this file is that the chapter's contract does not care: the
loader, the refusal, the probabilities and the sampler keep their shapes when
the amplitudes stop being complex.
"""

from __future__ import annotations

import numpy as np

from sampling import estimated_probability, sample_counts
from state import StateVector


class Coin:
    """Two weights that must sum to one, sampled with the same procedure."""

    def __init__(self, weights):
        values = np.asarray(list(weights), dtype=np.float64)
        if values.shape != (2,):
            raise ValueError(f"a two-outcome coin needs 2 weights, got {values.shape}")
        if np.any(values < 0):
            raise ValueError(f"weights cannot be negative: {values}")
        self._weights = values

    @property
    def weights(self):
        return self._weights.copy()

    def normalized(self):
        total = float(self._weights.sum())
        if total <= 0:
            raise ValueError("cannot normalize weights that sum to zero")
        return Coin(self._weights / total)

    def probabilities(self):
        return self.normalized()._weights

    def chance(self, index):
        if index not in (0, 1):
            raise ValueError(f"a coin has outcomes 0 and 1, got {index}")
        return float(self.probabilities()[index])


def main() -> None:
    coin = Coin([3, 1])
    print(f"weights:      {coin.weights}")
    print(f"probabilities: {coin.probabilities()}")

    # The same numbers as a quantum state with real, positive amplitudes.
    quantum = StateVector([np.sqrt(0.75), np.sqrt(0.25)])
    print()
    print(f"quantum p:     {quantum.probabilities()}")
    print(f"coin p:        {coin.probabilities()}")
    print(f"same numbers:  {np.allclose(quantum.probabilities(), coin.probabilities())}")

    print()
    coin_counts = sample_counts(StateVector(np.sqrt(coin.probabilities())), 1000, seed=2)
    print(f"coin counts:    {coin_counts}")
    print(f"quantum counts: {sample_counts(quantum, 1000, seed=2)}")
    print(f"frequency of 0: {estimated_probability(coin_counts, 0):.3f}")

    try:
        Coin([0, 0]).normalized()
    except ValueError as exc:
        print(f"refused: {exc}")


if __name__ == "__main__":
    main()
