"""Demo 04: compilation keeps the unitary and pays in depth.

Run: python3 chapters/chapter03/files/04_compile.py
"""

from circuit import Circuit
from compiler import check_basis, compiled_cost, compile_circuit

cases = {
    "bell (h, cx)": Circuit(2).add("h", 0).add("cx", 0, 1),
    "phase chain (h, t, h)": Circuit(1).add("h", 0).add("t", 0).add("h", 0),
    "five gates on one wire": Circuit(1).add("h", 0).add("t", 0).add("s", 0).add("x", 0).add("h", 0),
    "two wires in parallel": Circuit(2).add("h", 0).add("t", 1).add("x", 0).add("s", 1),
}

print(f"{'circuit':26s}{'ops':>10s}{'depth':>12s}{'ratio':>8s}{'distance':>11s}")
for name, circuit in cases.items():
    cost = compiled_cost(circuit)
    ops = f"{cost['ops_before']}->{cost['ops_after']}"
    depth = f"{cost['depth_before']}->{cost['depth_after']}"
    print(f"{name:26s}{ops:>10s}{depth:>12s}{cost['depth_ratio']:8.2f}{cost['distance']:11.2e}")

print()
compiled = compile_circuit(cases["bell (h, cx)"])
print(f"gates missing from the basis after compiling the bell: {check_basis(compiled) or 'none'}")
print(f"compiled bell ops: {[n for n, _, _ in compiled.ops]}")
