"""Demo 02: the oracle writes a sign, and the sign is what the algorithm reads.

Run: python3 chapters/chapter06/files/02_phase.py
"""

from algorithms import amplitude_pattern
from oracle import balanced, constant

for kind, f in (("constant 0", constant(0)), ("constant 1", constant(1)), ("balanced mask 1", balanced(1, 2))):
    pattern = amplitude_pattern(f, 2)
    signs = "".join("+" if value > 0 else "-" for value in pattern.values())
    print(f"{kind:16s} signs {signs}   amplitudes {[round(v, 3) for v in pattern.values()]}")

print()
print("with the output qubit in |->, the oracle multiplies amplitude x by (-1)^f(x)")
print("a constant f gives all plus; a balanced f gives a pattern with both signs")
print()
print("the final Hadamards turn 'all plus' into a peak at 00")
print("and any other sign pattern into a peak somewhere else")
