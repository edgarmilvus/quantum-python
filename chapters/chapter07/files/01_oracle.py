"""Demo 01: the oracle flips a sign, the diffusion flips about the mean.

Run: python3 chapters/chapter07/files/01_oracle.py
"""

import numpy as np

import grover

n = 3
marked = 5
state = grover.uniform(n)

print(f"uniform amplitudes (n={n}): {np.round(state, 3)}")
print(f"probabilities:              {np.round(grover.probabilities(state), 3)}")
print()

flipped = grover.oracle(marked, n) @ state
print(f"after the oracle on {marked}:  {np.round(flipped, 3)}")
mean = flipped.mean()
print(f"mean of the amplitudes:        {mean:.3f}")
print()

mirrored = grover.diffusion(n) @ flipped
print(f"after the diffusion:           {np.round(mirrored, 3)}")
others = [round(float(mirrored[i].real), 3) for i in range(len(mirrored)) if i != marked]
print(f"marked amplitude: {mirrored[marked].real:.3f}, others: {others[:3]}...")
print(f"probability of the marked item: {grover.probabilities(mirrored)[marked]:.4f}")
print()

print("the diffusion is 2|s><s| - I, so every amplitude becomes 2*mean - amplitude")
print(f"check on the marked entry: 2*{mean:.3f} - ({flipped[marked].real:.3f}) = {2*mean - flipped[marked].real:.3f}")
