"""Demo 01: the Hamiltonian, the exact answer, and the Hartree-Fock baseline.

Run: python3 chapters/chapter10/files/01_hamiltonian.py
"""

import numpy as np

import h2

print("H2 at 0.735 A, STO-3G, five terms plus the nuclear constant:")
for label, coefficient in h2.TERMS.items():
    print(f"  {label}  {coefficient:+.6f}")
print(f"  nuclear {h2.NUCLEAR:+.6f}")
print()

matrix = h2.hamiltonian()
print("the electronic Hamiltonian, four by four:")
print(np.round(matrix.real, 4))
print()
print(f"its eigenvalues (with the nuclear constant): {np.round(h2.exact_energies(), 6)}")
print()

hf = h2.energy(0.0)
exact = h2.exact_ground()
print(f"Hartree-Fock energy (theta = 0): {hf:.6f}")
print(f"exact ground state:              {exact:.6f}")
print(f"correlation energy:              {(exact - hf) * 1000:.2f} mHa")
print(f"chemical accuracy:               {h2.CHEMICAL_ACCURACY * 1000:.1f} mHa")
print()
print(f"in kcal/mol: correlation {h2.hartree_to_kcal(exact - hf):.2f}, "
      f"chemical accuracy {h2.hartree_to_kcal(h2.CHEMICAL_ACCURACY):.2f}")
