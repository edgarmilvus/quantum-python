"""Demo 05: correction amplifies noise, and here is the number.

Run: python3 chapters/chapter05/files/05_bias.py

Simulates 1024-shot data from a known distribution, corrects it with the measured
matrix, and compares the spread of the raw and the corrected estimate. The correction
removes bias and adds variance; both are visible in one table.
"""

import numpy as np

import calibrate
from stats import invert

TRUE = np.array([0.4268, 0.0732, 0.0732, 0.4268])  # the ideal Bell distribution at (0,45)
TRIALS = 2000
SHOTS = 1024


def main() -> None:
    record = calibrate.load()
    matrix = calibrate.matrix(record)
    inverse = invert(matrix)

    # The device sees the true distribution pushed through its own readout matrix.
    seen = matrix.T @ TRUE
    rng = np.random.default_rng(4)

    raw_values, corrected_values, clipped = [], [], []
    for _ in range(TRIALS):
        counts = rng.multinomial(SHOTS, seen)
        distribution = counts / SHOTS
        corrected, mass = calibrate.correct_distribution(distribution, inverse)
        raw_values.append(calibrate.expectation(distribution))
        corrected_values.append(calibrate.expectation(corrected))
        clipped.append(mass)

    raw = np.array(raw_values)
    fixed = np.array(corrected_values)

    print(f"true E at this setting: {calibrate.expectation(TRUE):.4f}")
    print(f"expected value read by the device: {calibrate.expectation(seen):.4f}")
    print()
    print(f"{'estimator':12s}{'mean':>10s}{'bias':>10s}{'spread':>10s}{'clipped':>10s}")
    print(f"{'raw':12s}{raw.mean():10.4f}{raw.mean() - calibrate.expectation(TRUE):10.4f}{raw.std(ddof=1):10.4f}{0.0:10.4f}")
    print(f"{'corrected':12s}{fixed.mean():10.4f}{fixed.mean() - calibrate.expectation(TRUE):10.4f}{fixed.std(ddof=1):10.4f}{np.mean(clipped):10.4f}")
    print()
    print(f"bias removed:  {abs(raw.mean() - calibrate.expectation(TRUE)) - abs(fixed.mean() - calibrate.expectation(TRUE)):+.4f}")
    print(f"spread added:  {fixed.std(ddof=1) - raw.std(ddof=1):+.4f}")


if __name__ == "__main__":
    main()
