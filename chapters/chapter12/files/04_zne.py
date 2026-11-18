"""Demo 04: zero-noise extrapolation, and the order the two steps go in.

Run: python3 chapters/chapter12/files/04_zne.py

Folding the Bell circuit to three and five copies triples and quintuples the
gate noise and leaves the ideal answer alone. Extrapolating to scale zero
removes the gate part — and only the gate part, which is why the readout
correction has to come first.
"""

import json
import math
from pathlib import Path

from noise import confusion, device, simulate, zne

ROOT = Path(__file__).resolve().parents[3]
S_IDEAL = 2 * math.sqrt(2)
matrix = device.readout_from_record().matrix()

record = json.loads((ROOT / "runs/0007-ibm-chsh/result.json").read_text())
fitted = {
    name: confusion.correlation(confusion.correct(counts, matrix)[0])
    for name, counts in record["counts"].items()
}
corrected_s = confusion.chsh(fitted)
rate = 1 - corrected_s / S_IDEAL

settings = {
    "ab": (0, 45),
    "ab_prime": (0, 135),
    "a_prime_b": (90, 45),
    "a_prime_b_prime": (90, 135),
}


def exact(scale: int, raw: bool) -> float:
    simulator = simulate.Simulator(rates=device.uniform_rates(single=0.0, two=rate), readout=None)
    correlators = {}
    for name, (alpha, beta) in settings.items():
        ops, basis = simulate.chsh_setting(alpha, beta)
        probabilities = simulator.distribution(2, zne.fold(ops, scale), basis)
        if raw:
            probabilities = matrix @ probabilities
        correlators[name] = (
            probabilities[0] + probabilities[3] - probabilities[1] - probabilities[2]
        )
    return confusion.chsh(correlators)


print(f"rate from the corrected CHSH: {rate:.5f}, one two-qubit gate per copy")
print(f"{'scale':>6s}{'gates':>7s}{'gate only':>11s}{'with readout':>14s}")
for scale in (1, 3, 5):
    print(f"{scale:6d}{scale:7d}{exact(scale, False):11.4f}{exact(scale, True):14.4f}")
print()

shots = 4096
sigma = 0.022
raw_points = [zne.Point(scale, exact(scale, True), sigma) for scale in (1, 3, 5)]
fixed_points = [zne.Point(scale, exact(scale, False), sigma) for scale in (1, 3, 5)]

print(f"{'pipeline':34s}{'S at scale 0':>14s}{'error':>10s}")
for label, points in (("ZNE on the raw values", raw_points),
                      ("readout, then ZNE (linear)", fixed_points),
                      ("readout, then ZNE (exponential)", fixed_points)):
    fit = zne.exponential(points) if label.endswith("exponential)") else zne.linear(points)
    print(f"{label:34s}{fit.value:14.4f}{fit.value - S_IDEAL:+10.4f}")
print(f"{'ideal':34s}{S_IDEAL:14.4f}{0.0:+10.4f}")
print()

linear_fit = zne.linear(fixed_points)
print(f"the linear weights at scales 1, 3, 5 are {[round(w, 3) for w in linear_fit.weights]}")
print(f"so the extrapolated error bar is {math.sqrt(sum(w * w for w in linear_fit.weights)):.3f} times one point's")
print(f"{sigma:.3f} at one point becomes {linear_fit.sigma:.3f} at scale zero: the correction's price")
print()

simulator = simulate.Simulator(rates=device.uniform_rates(single=0.0, two=rate), readout=None, seed=11)
sampled = []
for scale in (1, 3, 5):
    correlators = {}
    for name, (alpha, beta) in settings.items():
        ops, basis = simulate.chsh_setting(alpha, beta)
        counts = simulator.run(2, zne.fold(ops, scale), shots, basis=basis)
        distribution = {key: value / shots for key, value in counts.items()}
        correlators[name] = confusion.correlation(distribution)
    sampled.append(
        zne.Point(scale, confusion.chsh(correlators), confusion.chsh_sigma(correlators, shots))
    )

print(f"one sampled run, {shots} shots per setting, no readout in the model:")
for point in sampled:
    print(f"  scale {point.scale}: S = {point.value:.4f}")
print(f"  linear extrapolation: {zne.linear(sampled).report()}")
