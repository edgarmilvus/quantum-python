"""Demo 04: the resource count, at fifteen and at a real key.

Run: python3 chapters/chapter09/files/04_resources.py

The first table is the textbook count and this chapter's code implements it. The second
is a published estimate for RSA-2048, quoted as an estimate rather than re-derived.
"""

import order

print(f"{'N':>8s}{'bits':>6s}{'ancillas':>10s}{'qubits':>8s}{'multiplications':>16s}")
for n in (15, 21, 35, 143, 2048):
    row = order.circuit_resources(n)
    print(f"{row['n']:8d}{row['bits']:6d}{row['ancillas']:10d}{row['qubits']:8d}"
          f"{row['multiplications']:16d}")

print()
print("the textbook count for a 2048-bit modulus is 36 qubits and 300 multiplications")
print("that is the count for the arithmetic, not for the machine")
print()
print("published estimates for RSA-2048 (Gidney and Ekerå, 2021, and successors):")
print("  about 6,200 logical qubits")
print("  about 1e9 T gates, so hours on a machine with ~20 million physical qubits")
print()
print("the gap between 36 and 6,200 is error correction, which is chapter 16")
print()
print("what the chapter's code runs:")
for n in (15, 21, 35):
    bits = order.circuit_resources(n)["bits"]
    ancillas = order.circuit_resources(n)["ancillas"]
    print(f"  N={n:2d}: {bits + ancillas} qubits of state, {1 << (bits + ancillas):>7d} amplitudes")
