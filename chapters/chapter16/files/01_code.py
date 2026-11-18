"""Demo 01: three qubits, one bit, and the vote that decides.

Run: python3 chapters/chapter16/files/01_code.py

A single flip is invisible in the codeword and visible in the syndrome, and the
majority restores the bit. Two flips on three qubits are a majority for the wrong
answer, which is why the distance has to be odd and why the code's power is
counted in flips rather than in qubits.
"""

from ecc import code

for distance in (3, 5):
    instance = code.Repetition(distance)
    print(instance.report())
    print(f"  codeword for 0: {instance.encode(0)}")
    print(f"  codeword for 1: {instance.encode(1)}")
    print(f"  parity checks:  {instance.checks()}")
    print()

print("d=3, prepared 0, every single flip:")
instance = code.Repetition(3)
for position in range(3):
    bits = instance.encode(0)
    bits[position] ^= 1
    print(f"  flipped bit {position}: {bits}, syndromes {instance.syndromes(bits)}, "
          f"decoded {instance.decode(bits)}, correct {instance.decode(bits) == 0}")
print()

for flips in ([0, 1, 2], [0, 1, 2, 3, 4]):
    bits = [0] * 5
    for position in flips:
        bits[position] ^= 1
    broken = code.Repetition(5)
    print(f"  d=5, flips at {flips}: {bits}, decoded {broken.decode(bits)}, "
          f"correct {broken.decode(bits) == 0}, can correct {len(flips) <= broken.correctable}")
print()
print("the code's guarantee is a count of flips, not a rate:")
print(f"  d=3 corrects {code.Repetition(3).correctable} flip, d=5 corrects {code.Repetition(5).correctable}")
print(f"  a rate of 0.05 with n=3 gives a logical error of {code.logical_error_ideal(3, 0.05):.5f}")
print(f"  and with n=5, {code.logical_error_ideal(5, 0.05):.5f}")
