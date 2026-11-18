"""Demo 01: the quantum Fourier transform, against numpy's.

Run: python3 chapters/chapter08/files/01_dft.py
"""

import numpy as np

import qft

for n in (2, 3, 4):
    ours = qft.dft(n)
    theirs = np.fft.fft(np.eye(1 << n)) / np.sqrt(1 << n)
    print(f"n={n}: distance to numpy's unitary DFT = {np.max(np.abs(ours - np.transpose(theirs))):.2e}")

print()
matrix = qft.dft(3)
print("n=3, the transform of |0>:")
print(np.round(matrix @ np.array([1, 0, 0, 0, 0, 0, 0, 0]), 3))
print()
print("the transform of |1>:")
print(np.round(matrix @ np.array([0, 1, 0, 0, 0, 0, 0, 0]), 3))
print()
print("every basis state becomes the same magnitudes with different phases")
print(f"unitary: {np.allclose(matrix.conj().T @ matrix, np.eye(8))}")
print(f"inverse times forward: {np.max(np.abs(qft.dft(3, -1) @ matrix - np.eye(8))):.2e}")
