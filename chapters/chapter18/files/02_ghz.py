"""Demo 02: the same GHZ circuit on three sources.

Run: python3 chapters/chapter18/files/02_ghz.py

IBM's device, qBraid's gateway to an IonQ simulator, and an ideal sampler on this
machine. The distance, the wall time and the cost are in one table, and the table
has a trap: the qBraid row is exactly zero because the simulator returns
probabilities rather than samples.
"""

from bench import sources, task

rows = sources.ibm_ghz() + [sources.qbraid_ghz(), sources.local_ghz()]
print(task.table(rows))
print()

floor = task.noise_floor(4096, task.ideal_distribution(3))
print(f"the shot-noise floor at 4,096 shots: {floor:.4f}")
print()
print("the qBraid row is below the floor, which no sampler can be. The IonQ")
print("simulator returns exact probabilities and qBraid multiplies them by the shot")
print("count, so its histogram is the ideal distribution rounded; a distance of zero")
print("measures the reporting format, not a machine.")
print()

print("the simulated device, in the order the distances put them:")
for provider, value in sources.by_provider(rows).items():
    print(f"  {provider:8s}{value:.4f}")
print()
print("the IBM row at 20 microseconds of delay is in the same table and is not a")
print("different backend: same job, same qubits, a delay. Its distance nearly triples")
print("from 0.0681 to 0.1616, which is the benchmark measuring time rather than vendor.")
