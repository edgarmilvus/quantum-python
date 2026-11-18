"""Demo 03: the four Bell-pair sources the book recorded in its first chapters.

Run: python3 chapters/chapter18/files/03_bell.py

The same two-qubit circuit on a device, an exact emulator and an ideal simulator,
plus a sampler on this machine. The distances span 0.0537 to 0.0000 and the ranking
is the one the physics predicts: a real device loses to an emulator, and an
emulator loses to an exact answer.
"""

import numpy as np

from bench import sources, task

rows = sources.bell_rows()
ideal = {"00": 0.5, "11": 0.5}
rng = np.random.default_rng(0)
draws = rng.multinomial(1024, [0.5, 0.5])
counts = {"00": int(draws[0]), "11": int(draws[1])}
rows.append(
    task.Row(source="local ideal, sampled", provider="local", kind="sim",
             tvd=task.total_variation(counts, ideal), shots=1024,
             wall_seconds=0.01, cost_usd=0.0, notes="shot noise only")
)
print(task.table(rows))
print()
print(f"the floor at 1,024 shots: {task.noise_floor(1024, ideal):.4f}")
print()
print("the four sources, ranked:")
for provider, value in sources.by_provider(rows).items():
    print(f"  {provider:14s}{value:.4f}")
print()
print("and the improvement the device would need to match the emulator:")
device = next(row for row in rows if row.provider == "ibm")
emulator = next(row for row in rows if "inspire" in row.source)
print(f"  {device.tvd:.4f} / {emulator.tvd:.4f} = {device.tvd / emulator.tvd:.2f} times")
