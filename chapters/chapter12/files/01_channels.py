"""Demo 01: the three channels have three different signatures.

Run: python3 chapters/chapter12/files/01_channels.py

A state with both a coherence and a population difference (Ry(60) on |0>) shows
the difference. Depolarizing shrinks x and z together, amplitude damping moves
z toward +1 and shrinks x, and phase damping shrinks x and leaves z alone. A
mitigation that assumes the wrong channel repairs the wrong thing.
"""

import numpy as np

from noise import channels, states

print("a qubit tilted 60 degrees: Ry(pi/3)|0>, so x = 0.866 and z = 0.500")
print(f"{'channel':20s}{'p':>6s}{'P(0)':>8s}{'x':>9s}{'z':>9s}{'|rho01|':>9s}{'purity':>8s}")

tilted = states.apply(states.zero(1), states._gate("ry", np.pi / 3), (0,), 1)


def report(name: str, rho: np.ndarray, parameter: float) -> None:
    x, _, z = states.bloch(rho)
    print(
        f"{name:20s}{parameter:6.2f}{np.real(rho[0, 0]):8.4f}{x:9.4f}{z:9.4f}"
        f"{states.coherence(rho, 0, 1):9.4f}{states.purity(rho):8.4f}"
    )


report("ideal", tilted, 0.0)
for p in (0.05, 0.2, 0.5):
    report("depolarizing", channels.apply_channel(tilted, channels.depolarizing(p), (0,), 1), p)
for gamma in (0.05, 0.2, 0.5):
    report("amplitude damping", channels.apply_channel(tilted, channels.amplitude_damping(gamma), (0,), 1), gamma)
for lam in (0.05, 0.2, 0.5):
    report("phase damping", channels.apply_channel(tilted, channels.phase_damping(lam), (0,), 1), lam)

print()
print("the signatures, in one line each:")
print("  depolarizing  x and z shrink by the same factor")
print("  amplitude     z climbs toward +1 and x shrinks by sqrt(1-gamma)")
print("  phase         z is untouched and only x shrinks")

print()
print("every channel is trace preserving, which the sum of its Kraus operators shows:")
for name, operators in (
    ("depolarizing 0.2", channels.depolarizing(0.2)),
    ("amplitude 0.2", channels.amplitude_damping(0.2)),
    ("phase 0.2", channels.phase_damping(0.2)),
):
    count, distance = channels.channel_report(operators)
    print(f"  {name:18s}{count:2d} Kraus operators, ||sum K+K - 1|| = {distance:.2e}")

print()
print("a two-qubit depolarizing channel at p=0.1 keeps the Bell populations")
print("but cuts the coherence from 0.5000 to 0.4500, which is the (1-p) survival:")
bell = states.apply(states.zero(2), states._gate("h"), (0,), 2)
bell = states.apply(bell, states._gate("cx"), (0, 1), 2)
damaged = channels.apply_channel(bell, channels.depolarizing(0.1, 2), (0, 1), 2)
print(f"  populations {np.round(np.real(np.diag(damaged)), 4).tolist()}")
print(f"  coherence   {states.coherence(damaged, 0, 3):.4f}")
