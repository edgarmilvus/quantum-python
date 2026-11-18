"""Demo 05: why one axis is not enough, and where the surface code comes from.

Run: python3 chapters/chapter16/files/05_threshold.py

A depolarising channel has both error types, and the repetition code checks one. The
bit part falls with the distance and the phase part rises, so the total grows: at a
five percent depolarising rate the three-qubit code is worse than a bare qubit, and
a larger distance is worse still. That is the argument for the surface code, in one
table.
"""

from ecc import code, sim

print(f"{'p':>6s}{'bare qubit':>12s}{'d=3':>10s}{'d=5':>10s}{'d=7':>10s}")
for p in (0.01, 0.02, 0.05, 0.10):
    split = p / 2
    combined = [
        code.logical_error_ideal(d, split) + sim.phase_flip_error(d, split)
        for d in (3, 5, 7)
    ]
    print(f"{p:6.2f}{p:12.4f}{combined[0]:10.4f}{combined[1]:10.4f}{combined[2]:10.4f}")
print()
print("at p = 0.05 a bare qubit is wrong 5% of the time and the three-qubit code is")
print("wrong 7.3% of the time: the code paid three qubits to make things worse.")
print()
print("the reason is in the two columns of demo 03: the bit part of d=7 is 0.0002 and")
print("the phase part is 0.13, so the phase dominates and the extra qubits only add")
print("chances for it. A code with a threshold has to check both axes, which is what")
print("the surface code does with a two-dimensional lattice of data and syndrome qubits.")
print()
print("the threshold is the rate below which adding distance helps; for the surface")
print("code it is around one percent per operation, and this book's device sits at a")
print("few tenths of a percent per gate and one to three percent per readout, which is")
print("why a small surface code on today's hardware is a demonstration and not a")
print("machine.")
