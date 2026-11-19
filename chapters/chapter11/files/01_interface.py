"""Demo 01: one interface, and the four operations every provider implements.

Run: python3 chapters/chapter11/files/01_interface.py
"""

import providers as p

circuit = p.Circuit(2).add("h", 0).add("cx", 0, 1)

backend = p.Replay("chapter18/0001-bell-1024-ibm")
print(f"backend: {backend.provider} / {backend.name}")
profile = backend.profile()
print(f"profile: {profile.backend}, {profile.qubits} qubits, basis {profile.basis[:4]}...")
print()

job = backend.submit(circuit, shots=1024)
print(f"submit -> job {job.id} ({job.shots} shots, depth {job.depth}, replay={job.replay})")
print(f"status -> {backend.status(job)}")
result = backend.result(job)
print(f"result -> {dict(sorted(result.counts.items()))}")
print(f"frequency of 10: {result.frequency('10'):.4f}")
print()

print("the same four calls work for every provider in the registry:")
print(f"  submit(circuit, shots) -> Job")
print(f"  status(job)            -> str")
print(f"  result(job)            -> Result")
print(f"  cancel(job)            -> None or BackendError")
print()
print(f"providers known: {sorted(p.SPECS)}")
print(f"providers ready: {p.configured()}")
