"""Demo 05: one state, four implementations, one number.

Run: python3 chapters/chapter01/files/05_three_sdks.py
"""

import numpy as np

from sdks import compare

amplitudes = [np.sqrt(0.6), np.sqrt(0.4) * 1j]

print(f"reference amplitudes: {amplitudes}")
print()
print(f"{'implementation':14s} {'largest difference':>20s}   state")
for name, produced, distance in compare(amplitudes):
    print(f"{name:14s} {distance:20.3e}   {np.round(produced, 6)}")

print()
print("agreement is a number, not an opinion")
