"""Demo 03: S on an ideal pair, against both bounds.

Run: python3 chapters/chapter04/files/03_chsh.py
"""

import bell

simulated = bell.simulate()
print(f"{'setting':16s}{'E':>10s}")
for name, value in simulated.items():
    print(f"{name:16s}{value:10.4f}")

s = bell.chsh(simulated)
print()
print(f"S = {s:.6f}")
print(f"classical bound: {bell.CLASSICAL_BOUND:.6f}   margin {s - bell.CLASSICAL_BOUND:+.6f}")
print(f"Tsirelson bound: {bell.TSIRELSON_BOUND:.6f}   gap {bell.TSIRELSON_BOUND - s:+.2e}")
print()

# A pair of independent qubits cannot do this: their E factorizes.
independent = {"ab": 0.0, "ab_prime": 0.0, "a_prime_b": 0.0, "a_prime_b_prime": 0.0}
print(f"S for two independent qubits: {bell.chsh(independent):.6f}")
