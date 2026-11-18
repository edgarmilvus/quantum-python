"""Demo 05: the QFT is not a faster FFT, and the cost table says why.

Run: python3 chapters/chapter08/files/05_classical.py

A classical FFT of N numbers costs about N log N operations and returns N amplitudes.
The quantum transform costs n^2 gates and returns one sample. The comparison is a
category error, and the table is the honest way to show it.
"""

import math

import qft

print(f"{'N':>6s}{'classical FFT':>16s}{'QFT gates':>12s}{'QFT depth':>11s}")
for n in (4, 8, 12, 16, 20):
    size = 1 << n
    classical = size * n
    print(f"{size:6d}{classical:16d}{qft.gate_count(n):12d}{qft.circuit_depth(n):11d}")

print()
print("the classical number is operations on one machine; the quantum number is gates on a device")
print("more importantly, the classical FFT returns every amplitude and the QFT returns one sample")
print()
print("what the QFT is for: turning a phase into a bit string, which is what phase estimation does")
print()
print(f"a twenty-qubit transform has {qft.gate_count(20)} gates and depth {qft.circuit_depth(20)}")
print(f"its matrix would have {((1 << 20) ** 2):,} entries and would never be built")
