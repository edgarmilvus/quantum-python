"""Demo 02: depth counts layers, not gates.

Run: python3 chapters/chapter03/files/02_depth.py
"""

from circuit import Circuit

sequential = Circuit(2).add("h", 0).add("x", 0).add("y", 0).add("z", 0)
parallel = Circuit(2).add("h", 0).add("x", 1).add("y", 0).add("z", 1)

for name, circuit in (("all on wire 0", sequential), ("alternating wires", parallel)):
    print(f"{name}: {circuit.gate_count()} gates, depth {circuit.depth()}")
    for index, layer in enumerate(circuit.layers(), start=1):
        print(f"  layer {index}: {[n + str(list(w)) for n, w, _ in layer]}")

print()
print("the same number of gates, half the depth" if parallel.depth() < sequential.depth() else "same depth")
print()
print("two gates on the same wire cannot share a layer; two on different wires can")
