"""Demo 05: a local hidden-variable program, and the bound it cannot pass.

This is the competitor. Two agents share a random variable, each answers from the
setting they were given and the variable they hold, and nothing else. Whatever they
do, S stays at or below 2. Running the program is how the reader sees that the bound
is arithmetic rather than a property of devices.

Run: python3 chapters/chapter04/files/05_local_model.py
"""

import numpy as np

import bell

SAMPLES = 200_000
ANGLES = np.radians([0.0, 90.0])          # a, a'
SETTINGS_B = np.radians([45.0, 135.0])    # b, b'


def answer(setting: float, hidden: float) -> int:
    """One agent's deterministic answer: +1 or -1, from its angle and the hidden bit."""
    return 1 if np.cos(setting - hidden) >= 0 else -1


def expectation(setting_a: float, setting_b: float, rng) -> float:
    """E estimated from shared hidden variables."""
    hidden = rng.uniform(0.0, 2.0 * np.pi, size=SAMPLES)
    left = np.where(np.cos(setting_a - hidden) >= 0, 1, -1)
    right = np.where(np.cos(setting_b - hidden) >= 0, 1, -1)
    return float(np.mean(left * right))


def main() -> None:
    rng = np.random.default_rng(5)
    values = {}
    for name, angle_a, angle_b in (
        ("ab", ANGLES[0], SETTINGS_B[0]),
        ("ab_prime", ANGLES[0], SETTINGS_B[1]),
        ("a_prime_b", ANGLES[1], SETTINGS_B[0]),
        ("a_prime_b_prime", ANGLES[1], SETTINGS_B[1]),
    ):
        values[name] = expectation(angle_a, angle_b, rng)

    print(f"{'setting':16s}{'E (local model)':>18s}")
    for name, value in values.items():
        print(f"{name:16s}{value:18.4f}")

    s = bell.chsh(values)
    error = bell.chsh_error(values, SAMPLES)
    print()
    print(f"S from the local model: {s:.4f} +/- {error:.4f}")
    print(f"classical bound:        {bell.CLASSICAL_BOUND:.4f}")
    print(f"margin:                 {s - bell.CLASSICAL_BOUND:+.4f} ({(s - bell.CLASSICAL_BOUND) / error:.1f} sigma)")
    print(f"exceeds the bound by more than 3 sigma: {s - bell.CLASSICAL_BOUND > 3 * error}")
    print()
    print("a quantum pair reaches 2.828 with the same combination of settings")
    print("the local model stays at 2.00 however many samples it draws")


if __name__ == "__main__":
    main()
