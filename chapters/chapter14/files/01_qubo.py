"""Demo 01: the same problem in bits and in spins.

Run: python3 chapters/chapter14/files/01_qubo.py

MaxCut becomes a QUBO whose energy is minus the cut, so the minimum energy is
minus the maximum cut. The QUBO becomes an Ising model with no local fields,
because a unit-weight cut has no preference for one side. Then a denser instance,
where the brute force still answers but the landscape is no longer a graph.
"""

from anneal import instances, qubo, sampler

small = qubo.qubo_from_maxcut(instances.maxcut_square(), 4)

print("MaxCut on four vertices as a QUBO:")
print(qubo.report(small))
print()
print(f"{'bits':8s}{'energy':>8s}{'minus energy':>14s}")
for bits, value in qubo.all_energies(small, 4).items():
    print(f"{format(bits, '04b'):8s}{value:8.0f}{(0.0 if value == 0 else -value):14.0f}")
print()

best_value, assignment = qubo.brute_force(small, 4)
bits = sum(bit << index for index, bit in assignment.items())
print(f"minimum energy {best_value:.0f} at {format(bits, '04b')}, which is a cut of {-best_value:.0f}")
print("the identity the harness asserts: energy(x) = -cut(x) for all sixteen assignments")
print()

linear, coupling, offset = qubo.to_ising(small)
print(f"the Ising form: {len(linear)} local fields, {len(coupling)} couplings, offset {offset:g}")
print("no local fields, because a unit-weight cut treats both sides the same")
print(f"offset {offset:g} is what the substitution adds and what a machine subtracts")
print()

print("a denser instance: twelve variables, every pair coupled, signs drawn once")
spin_glass = instances.spin_glass()
print(f"  {len(spin_glass)} couplings, no local fields, weights plus or minus one")
exact = sampler.Exact({}, spin_glass).sample()
print(f"  minimum energy {exact.best()[0]:.0f} at spins {''.join(str(s) for _, s in sorted(exact.best()[1].items()))}")
print(f"  {int(exact.info['ground states'])} assignments reach it, out of 4,096")
print("  this is the instance demo 02 anneals, and it has no graph in it at all")
print()
print("the same dictionary means two things: as a QUBO it is read with bits,")
print("as a coupling map it is read with spins, and the two minima differ.")
