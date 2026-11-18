"""Demo 02: the same expectation from probabilities and from shots.

Run: python3 chapters/chapter04/files/02_expectations.py
"""

import numpy as np

import bell

angle_a, angle_b = 0.0, 45.0
p = bell.probabilities(angle_a, angle_b)
print(f"p = {np.round(p, 4)}")
print(f"E from probabilities: {bell.expectation_from_probabilities(p):.6f}")
print(f"predicted cos(a-b):   {bell.predicted_expectation(angle_a, angle_b):.6f}")
print()

print(f"{'shots':>8s}{'E from counts':>16s}{'1 sigma':>12s}")
for shots in (100, 1000, 10000, 100000):
    rng = np.random.default_rng(11)
    draws = rng.choice(4, size=shots, p=p)
    counts = {"00": 0, "01": 0, "10": 0, "11": 0}
    for draw in draws:
        counts[format(int(draw), "02b")] += 1
    value = bell.expectation_from_counts(counts)
    print(f"{shots:8d}{value:16.4f}{bell.standard_error(value, shots):12.4f}")

print()
print("the estimate moves toward 0.7071 as the shots grow, and its error bar shrinks")
