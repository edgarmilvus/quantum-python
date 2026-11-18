"""Demo 02: the circuit is Hadamards and phases, and its cost grows as n squared.

Run: python3 chapters/chapter08/files/02_circuit.py
"""

import numpy as np

import qft

print(f"{'n':>2s}{'gates':>8s}{'depth':>8s}{'distance to DFT':>18s}")
for n in (1, 2, 3, 4, 5, 6):
    distance = np.max(np.abs(qft.qft_matrix(n) - qft.dft(n)))
    print(f"{n:2d}{qft.gate_count(n):8d}{qft.circuit_depth(n):8d}{distance:18.2e}")

print()
print("gates = n + n(n-1)/2 + n/2: Hadamards, controlled phases, and the swaps")
print("the swaps exist only because of the bit order the circuit produces")
print()
for n in (3, 4):
    print(f"n={n} ops in order:")
    names = []
    for j in range(n):
        names.append(f"H{j}")
        for k in range(j + 1, n):
            names.append(f"CP({k},{j})")
    for j in range(n // 2):
        names.append(f"SWAP({j},{n - 1 - j})")
    print("  " + " ".join(names))
