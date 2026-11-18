"""Demo 05: the contract a real annealer would satisfy, and what stays empty.

Run: python3 chapters/chapter14/files/05_dwave.py

D-Wave's cloud stack is a sampler behind an HTTP endpoint: a problem is submitted
as linear biases and couplings, the response carries samples, energies and
occurrence counts, and the hardware adds chain-break fractions, a timing block
and a problem id. This chapter implements the first three and leaves the last
three empty on purpose, because the Trial plan stopped issuing tokens in 2026
and a chapter that cannot run on a machine should not pretend it did.
"""

from anneal import embed, instances, sampler

linear: dict = {}
coupling = instances.spin_glass()
exact = sampler.Exact(linear, coupling).sample()
optimum = exact.best()[0]

print("what this chapter's sampler returns:")
result = sampler.Annealer(linear, coupling, 0.0, sweeps=300, seed=11).sample(200)
print(f"  samples      {len(result.samples)} distinct spin assignments")
print(f"  energies     {[round(value, 1) for value in result.energies[:4]]} ...")
print(f"  occurrences  {result.occurrences[:4]} ...")
print(f"  reads        {result.reads}, which is the sum of the occurrences")
print(f"  info         {sorted(result.info)}")
print()
print("what a hardware sample set would add, and this one leaves empty:")
for field in ("chain_break_fraction", "timing", "problem_id"):
    print(f"  {field:22s} absent: no machine was programmed")
print()
print(f"the local sampler finds the optimum {optimum:.0f} on "
      f"{sampler.success_rate(result, optimum):.1%} of its reads")
print()

print("the same contract on the embedded problem, where the two extra fields matter:")
graph = embed.Chimera(2, 2)
logical_linear, logical_coupling, embedding = embed.five_variable_instance()
physical_linear, physical_coupling = embed.physical_problem(
    logical_linear, logical_coupling, embedding, 0.2, graph
)
physical = sampler.Annealer(physical_linear, physical_coupling, 0.0, sweeps=300, seed=5).sample(50)
fractions = [
    embed.chain_break_fraction(sample, embedding) for sample in physical.samples
]
print(f"  chain_break_fraction per distinct sample: {[round(value, 2) for value in fractions]}")
print(f"  mean over the run: {sum(f * c for f, c in zip(fractions, physical.occurrences)) / physical.reads:.3f}")
print()
print("that number is the one a real machine reports and a simulator has to compute.")
print("On the hardware it comes from the qubits; here it comes from the same sample.")
print()
print("what a QPU would change, and what it would not:")
print(f"  {'measured here':38s}{'would need a machine'}")
print(f"  {'the QUBO and its optimum':38s}{'nothing'}")
print(f"  {'the embedding and its chains':38s}{'nothing, but the real topology is Pegasus'}")
print(f"  {'chain-break rate at a strength':38s}{'the coupling errors and the flux noise'}")
print(f"  {'success probability per read':38s}{'the anneal time, the schedule, the temperature'}")
print(f"  {'wall time per read':38s}{'the queue and the programming cycle'}")
