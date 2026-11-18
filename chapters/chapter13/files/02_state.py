"""Demo 02: what the optimal one-layer state actually looks like.

Run: python3 chapters/chapter13/files/02_state.py

The angles are the ones demo 04's optimiser finds for p=1: beta 0.3109 and gamma
0.5713. At that point the circuit puts 32.8% of its probability on the two
optimal cuts, against 12.5% for a uniform guess, and raises the expected cut
from 2.5 to 3.24.
"""

import numpy as np

from qaoa import graph as g, qaoa, state as st

instance = g.square_with_diagonal()
optimum, _ = instance.max_cut()
beta, gamma = 0.3109, 0.5713
vector = qaoa.state_for(instance, [beta], [gamma])

print(f"angles: beta {beta}, gamma {gamma}, p = 1")
print(f"norm {st.norm(vector):.12f}, which the harness asserts is 1")
print()

probabilities = st.probabilities(vector)
print(f"{'bits':8s}{'cut':>5s}{'probability':>13s}")
for bits in range(2 ** instance.n):
    if probabilities[bits] > 0.005:
        print(f"{format(bits, '04b'):8s}{instance.cut(bits):5g}{probabilities[bits]:13.4f}")
print()

print("grouped by cut value, which is what a histogram of the experiment shows:")
for value, probability in qaoa.distribution_over_cuts(instance, vector).items():
    bar = "#" * int(round(probability * 40))
    print(f"  cut {value:g}: {probability:6.4f}  {bar}")
print()

mean = qaoa.expected_cut(instance, vector)
print(f"expected cut {mean:.4f} of an optimum {optimum:g}")
print(f"approximation ratio {qaoa.approximation_ratio(mean, optimum):.4f}")
print()
print("the two optimal assignments take 0.1641 each, so a single shot lands on one")
print("of them 32.8% of the time against 12.5% for a coin flip.")

print()
zero = qaoa.state_for(instance, [0.0], [0.0])
print(f"at beta = gamma = 0 the state is the uniform superposition:")
print(f"  expected cut {qaoa.expected_cut(instance, zero):.4f}, the uniform mean {instance.uniform_mean():g}")
print("which is the control: with no phase separator and no mixer, QAOA is guessing.")
