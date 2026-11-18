"""Demo 02: why the simulator has to collapse, and what an ancilla costs.

Run: python3 chapters/chapter17/files/02_collapse.py

A circuit with a mid-circuit measurement is not a circuit with a measurement at the
end. The ancilla is measured while the data qubit is still in a superposition, the
conditional gate acts on the outcome, and a simulator that measured everything at
the end would report the joint distribution of two qubits that were never
conditioned on anything.
"""

from dyn import sim

ops = [
    ("h", (0,)),
    ("cx", (0, 1)),
    ("measure", (1,), 2),
    ("if", (2, 1), [("x", (0,))]),
    ("measure", (0,), 0),
]

total = 4000
joint = sim.histogram(ops, total, bits=(2, 0), seed=5)
print("Hadamard on the data, CNOT onto the ancilla, measure the ancilla into bit 2,")
print("flip the data if the ancilla was 1, then measure the data into bit 0:")
for key, count in sorted(joint.items()):
    print(f"  ancilla {key[0]}, data {key[1]}: {count / total:.3f}")
print()

print("the data qubit is 0 in every shot: the ancilla said which branch the pair")
print("was in, and the conditional undid it. The joint distribution of the two")
print("qubits before the measurement was a Bell pair, so a simulator that measured")
print("at the end would have printed ancilla 0/data 0 and 1/1 in equal measure.")
print()

no_conditional = [
    ("h", (0,)),
    ("cx", (0, 1)),
    ("measure", (1,), 2),
    ("measure", (0,), 0),
]
plain = sim.histogram(no_conditional, total, bits=(2, 0), seed=5)
print("the same circuit without the conditional, for comparison:")
for key, count in sorted(plain.items()):
    print(f"  ancilla {key[0]}, data {key[1]}: {count / total:.3f}")
print()
print("that is the pair a final-measurement simulator would confuse for the")
print("conditional one, and the difference between the two tables is the whole")
print("reason a dynamic circuit needs its own kind of simulator.")
