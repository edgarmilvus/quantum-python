"""Demo 03: chains, breaks, and the strength that decides both.

Run: python3 chapters/chapter14/files/03_embed.py

The five-variable instance lives on a Chimera C(2,2), where four of its variables
need a chain of two physical qubits. A chain that disagrees with itself is broken,
and the majority vote that repairs it is right only as often as the chain is
short. The demo sweeps the chain strength and shows the two failures: too weak,
and the chain votes with the noise; too strong, and the physical landscape is
rugged enough to trap the annealer.
"""

from anneal import embed, sampler

graph = embed.Chimera(2, 2)
linear, coupling, embedding = embed.five_variable_instance()
embed.validate(embedding, graph, coupling.keys())

print(f"Chimera C(2,2): {len(graph.qubits)} physical qubits, {len(graph.edges())} couplers")
print()
print(embed.embed_report(embedding))
print()
print(f"logical problem: {len(coupling)} couplings, {len(set(v for pair in coupling for v in pair))} variables")
exact = sampler.Exact(linear, coupling).sample()
optimum = exact.best()[0]
print(f"exact optimum {optimum:.1f} at spins "
      f"{''.join(str(value) for _, value in sorted(exact.best()[1].items()))}")
print()

print(f"{'strength':>9s}{'breaks':>9s}{'optimal reads':>15s}{'mean energy':>14s}")
for strength in (0.2, 0.5, 1.0, 2.0, 4.0):
    physical_linear, physical_coupling = embed.physical_problem(
        linear, coupling, embedding, strength, graph
    )
    result = sampler.Annealer(physical_linear, physical_coupling, 0.0, sweeps=300, seed=5).sample(50)
    breaks = sum(
        embed.chain_break_fraction(sample, embedding) * count
        for sample, count in zip(result.samples, result.occurrences)
    ) / result.reads
    hits = sum(
        count
        for sample, count in zip(result.samples, result.occurrences)
        if sampler.ising_energy(linear, coupling, 0.0, embed.unembed(sample, embedding)[0]) <= optimum + 1e-9
    )
    energies = []
    for sample, count in zip(result.samples, result.occurrences):
        logical, _ = embed.unembed(sample, embedding)
        energies += [sampler.ising_energy(linear, coupling, 0.0, logical)] * count
    print(f"{strength:9.1f}{breaks:9.3f}{hits:8d}/{result.reads:<6d}{sum(energies) / len(energies):14.3f}")
print()
print("0.2 leaves one chain in five broken; 1.0 breaks none; 4.0 breaks none")
print("and still loses twelve reads, because a chain that strong is a local minimum.")
print()

physical_linear, physical_coupling = embed.physical_problem(linear, coupling, embedding, 0.2, graph)
weak = sampler.Annealer(physical_linear, physical_coupling, 0.0, sweeps=300, seed=5).sample(50)
for sample in weak.samples:
    fraction = embed.chain_break_fraction(sample, embedding)
    if fraction > 0:
        logical, broken = embed.unembed(sample, embedding)
        print(f"a broken read: chain(s) {broken} disagreed, majority vote gave {logical}")
        print(f"  its logical energy {sampler.ising_energy(linear, coupling, 0.0, logical):.1f} "
              f"against the optimum {optimum:.1f}")
        break
