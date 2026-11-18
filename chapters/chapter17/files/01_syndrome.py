"""Demo 01: the syndrome, the correction, and a simulator that has to collapse.

Run: python3 chapters/chapter17/files/01_syndrome.py

The circuit measures two ancillas in the middle and applies a Pauli conditioned on
their value. On a noiseless simulator the correction repairs every single flip and
none of the doubles, which is the code's guarantee, and the control without the
correction repairs nothing.
"""

from dyn import circuit, sim

TARGET = {1: 0, 3: 1, 2: 2}

print("the circuit for a clean codeword:")
for op in circuit.memory(prepared=1, correct=True):
    print(f"  {op[0]:8s}{op[1]}")

print()
print("the syndrome of every single flip, and the qubit the table corrects:")
for position in range(3):
    bits = [0, 0, 0]
    bits[position] = 1
    parity = tuple((bits[i] + bits[i + 1]) % 2 for i in range(2))
    value = parity[0] + 2 * parity[1]
    print(f"  flip at {position}: syndrome {parity}, register value {value}, correct qubit {TARGET[value]}")
print()

print("the local simulator, 500 shots each:")
print(f"{'error':>12s}{'corrected':>12s}{'control':>10s}")
for flips in ((), (0,), (1,), (2,), (0, 1)):
    fixed = sim.sample(circuit.memory(prepared=0, correct=True, flips=flips), 500, seed=4)
    loose = sim.sample(circuit.memory(prepared=0, correct=False, flips=flips), 500, seed=4)
    label = "none" if not flips else "flip " + ",".join(str(f) for f in flips)
    print(f"{label:>12s}{fixed.get('000', 0) / 500:12.3f}{loose.get('000', 0) / 500:10.3f}")
print()
print("a single flip comes back clean only with the correction; two flips are a")
print("majority for the wrong answer, which is the code's limit and not a bug.")
