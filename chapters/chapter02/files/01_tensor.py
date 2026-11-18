"""Demo 01: two qubits are four amplitudes, built by a nested loop or by kron.

Run: python3 chapters/chapter02/files/01_tensor.py
"""

import numpy as np

from register import Register

left = np.array([1.0, 0.0])
right = np.array([0.0, 1.0])

by_loop = [a * b for a in left for b in right]
by_kron = np.kron(left, right)

print(f"nested loop: {np.round(by_loop, 3)}")
print(f"kron:        {np.round(by_kron, 3)}")
print(f"equal:       {np.allclose(by_loop, by_kron)}")
print()

register = Register.tensor(left, right)
print(f"labels:      {register.labels()}")
print(f"amplitudes:  {np.round(register.amplitudes, 3)}")
print(f"p:           {register.probabilities()}")
print()

superposed = Register.tensor(np.array([np.sqrt(0.5), np.sqrt(0.5)]), np.array([1.0, 0.0]))
print(f"|+> tensor |0>: {np.round(superposed.amplitudes, 3)}")
print(f"p:              {np.round(superposed.probabilities(), 3)}")
print(f"labels:         {superposed.labels()}")
