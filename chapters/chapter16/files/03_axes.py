"""Demo 03: the code protects one axis and amplifies the other.

Run: python3 chapters/chapter16/files/03_axes.py

A bit flip is what the vote sees and corrects. A phase flip leaves every codeword
bit alone, so the vote is blind to it and the logical phase is the parity of the
errors: the more qubits, the more chances to be wrong. The two columns move in
opposite directions with the distance, and that is why a real code needs a second
dimension.
"""

from ecc import code, sim

print(f"{'p':>6s}{'':4s}{'d=3':>10s}{'d=5':>10s}{'d=7':>10s}")
for p in (0.01, 0.05, 0.10, 0.20):
    bit = [code.logical_error_ideal(d, p) for d in (3, 5, 7)]
    phase = [sim.phase_flip_error(d, p) for d in (3, 5, 7)]
    print(f"{p:6.2f}    bit  {bit[0]:10.5f}{bit[1]:10.5f}{bit[2]:10.5f}")
    print(f"{'':6s}    phase{phase[0]:10.5f}{phase[1]:10.5f}{phase[2]:10.5f}")
print()

print("at p = 0.05 the bit column falls by a factor of six from d=3 to d=7,")
print("and the phase column rises by a factor of two:")
p = 0.05
print(f"  bit   d=3 {code.logical_error_ideal(3, p):.4f}  d=7 {code.logical_error_ideal(7, p):.4f}"
      f"   ratio {code.logical_error_ideal(7, p) / code.logical_error_ideal(3, p):.3f}")
print(f"  phase d=3 {sim.phase_flip_error(3, p):.4f}  d=7 {sim.phase_flip_error(7, p):.4f}"
      f"   ratio {sim.phase_flip_error(7, p) / sim.phase_flip_error(3, p):.3f}")
print()
print("a depolarising channel has both, so a repetition code's total error has a")
print("minimum at some distance and grows after it; the surface code is what removes")
print("the minimum by checking both axes at once.")
