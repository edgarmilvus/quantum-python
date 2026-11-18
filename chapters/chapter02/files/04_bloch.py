"""Demo 04: the Bloch vector of four states, computed and then measured.

Run: python3 chapters/chapter02/files/04_bloch.py
"""

import numpy as np

from bloch import angle_deg, bloch_vector, measurement_basis, estimate_vector, purity, ry_angle_deg
from gates import H, Ry, apply_one

states = {
    "|0>": np.array([1.0, 0.0]),
    "|1>": np.array([0.0, 1.0]),
    "H|0>": apply_one(np.array([1.0, 0.0]), H, 0, wires=1),
    "Ry(60)|0>": apply_one(np.array([1.0, 0.0]), Ry(np.pi / 3), 0, wires=1),
}

print(f"{'state':12s}{'bloch':>28s}{'|r|':>8s}{'azimuth':>10s}")
for name, state in states.items():
    vector = bloch_vector(state)
    azimuth = angle_deg(state) if not np.allclose(vector[:2], 0) else float("nan")
    print(f"{name:12s}{str(np.round(vector, 4)):>28s}{purity(state):8.4f}{azimuth:10.1f}")

print()
print(f"Ry angle recovered: {ry_angle_deg(states['Ry(60)|0>']):.1f} degrees (built with 60)")

print()
print("measured, 2000 shots per axis, seed 11:")
counts_by_axis = {}
for axis in ("x", "y", "z"):
    rotated = apply_one(states["Ry(60)|0>"], measurement_basis(axis), 0, wires=1)
    p0 = float(np.abs(rotated[0]) ** 2)
    rng = np.random.default_rng(11)
    draws = (rng.random(2000) >= p0).sum()
    counts_by_axis[axis] = {"0": 2000 - int(draws), "1": int(draws)}
    print(f"  {axis}: {counts_by_axis[axis]}")

estimated = estimate_vector(counts_by_axis)
truth = bloch_vector(states["Ry(60)|0>"])
print()
print(f"estimated: {np.round(estimated, 4)}")
print(f"truth:     {np.round(truth, 4)}")
