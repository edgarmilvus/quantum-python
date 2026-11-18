"""Demo 02: the multiplier as a permutation, and the phases that carry the order.

Run: python3 chapters/chapter09/files/02_permutation.py
"""

import numpy as np

import order

a, n, bits = 7, 15, 4
matrix = order.multiplier_matrix(a, n, bits)
print(f"the multiplier by {a} modulo {n} on 16 states:")
print(matrix.real.astype(int))
print()

print("it is a permutation, and the states at or above N are fixed:")
print(f"  row sums: {np.unique(matrix.sum(axis=1))}, column sums: {np.unique(matrix.sum(axis=0))}")
print()

squared = order.power_matrix(matrix, 2)
print(f"the square maps 1 to {int(np.argmax(squared[:, 1]))}, which is {a * a} mod {n}")
fourth = order.power_matrix(matrix, 4)
print(f"the fourth power is the identity: {np.allclose(fourth, np.eye(16))}")
print()

eigenvalues = np.linalg.eigvals(matrix)
angles = sorted({round(float(np.angle(value)) / (2 * np.pi), 6) for value in eigenvalues})
print(f"the distinct eigenphases, in turns: {angles}")
print(f"there are {len(angles)} of them, and they are multiples of 1/{order.order_of(a, n)}")
print()
print("phase estimation on this permutation returns one of those multiples")
