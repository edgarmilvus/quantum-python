"""Demo 02: one fitted rate, three predictions.

Run: python3 chapters/chapter12/files/02_simulate.py

The rate comes from one number: the readout-corrected CHSH value, which leaves
the gate contribution alone. With that single parameter the model reproduces
the raw CHSH value and the Bell pair's correlation, both of which it was not
fitted to. The third prediction is Grover, and demo 05 shows what happens there.
"""

import json
import math
from pathlib import Path

from noise import confusion, device, fit, simulate

S_IDEAL = 2 * math.sqrt(2)
ROOT = Path(__file__).resolve().parents[3]

matrix = device.readout_from_record().matrix()
record = json.loads((ROOT / "runs/0007-ibm-chsh/result.json").read_text())
correlators = {
    name: confusion.correlation(confusion.correct(counts, matrix)[0])
    for name, counts in record["counts"].items()
}
chsh_corrected = confusion.chsh(correlators)

rate = 1 - chsh_corrected / S_IDEAL
print(f"readout-corrected CHSH: {chsh_corrected:.4f} of an ideal {S_IDEAL:.4f}")
print(f"one gate rate that explains it: {rate:.5f} per two-qubit gate")
print()

settings = {
    "ab": (0, 45),
    "ab_prime": (0, 135),
    "a_prime_b": (90, 45),
    "a_prime_b_prime": (90, 135),
}


def chsh(raw: bool) -> float:
    """The four correlators, with or without the readout matrix on the end."""
    simulator = simulate.Simulator(rates=device.uniform_rates(single=0.0, two=rate), readout=None)
    correlators = {}
    for name, (alpha, beta) in settings.items():
        ops, basis = simulate.chsh_setting(alpha, beta)
        probabilities = simulator.distribution(2, ops, basis)
        if raw:
            probabilities = matrix @ probabilities
        correlators[name] = (
            probabilities[0] + probabilities[3] - probabilities[1] - probabilities[2]
        )
    return confusion.chsh(correlators)


print(f"{'quantity':22s}{'model':>10s}{'recorded':>10s}{'gap':>9s}")
print(f"{'CHSH, gate only':22s}{chsh(False):10.4f}{chsh_corrected:10.4f}{chsh(False) - chsh_corrected:+9.4f}")
raw_recorded = sum(record["counts"]["ab"].values())
raw_chsh = confusion.chsh({name: confusion.correlation({k: v / raw_recorded for k, v in counts.items()}) for name, counts in record["counts"].items()})
print(f"{'CHSH, raw':22s}{chsh(True):10.4f}{raw_chsh:10.4f}{chsh(True) - raw_chsh:+9.4f}")

bell = simulate.Simulator(rates=device.uniform_rates(single=0.0, two=rate), readout=None)
probabilities = matrix @ bell.distribution(2, simulate.bell())
model = float(probabilities[0] + probabilities[3])
print(f"{'Bell, correlated':22s}{model:10.4f}{0.9463:10.4f}{model - 0.9463:+9.4f}")
print()

sigma = device.sigma_binomial(0.9463, 1024)
print(f"the Bell gap is {abs(model - 0.9463):.4f} against a shot error of {sigma:.4f}")
print(f"that is {abs(model - 0.9463) / sigma:.2f} sigma, so the model survives its first test")
print()
print("the same rate, on Grover's 45 two-qubit gates:")
grover = fit.predict(rate, 45)
print(f"  survival {grover:.4f}, peak {fit.peak(0.9453, grover):.4f}")
print("  the device reported 0.7148 raw and 0.7649 after readout correction")
print("  demo 05 shows why the prediction is off by a factor, and what replaces it")
