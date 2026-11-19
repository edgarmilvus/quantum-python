"""Submit the four CHSH settings to IBM Quantum and record the counts.

One job, four circuits, 1024 shots each. Writes runs/chapter04/0007-chsh-1024-ibm/result.json.
"""

import json
import math
import os
import pathlib
import sys

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

from qiskit import QuantumCircuit, transpile
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

SETTINGS = {
    "ab": (0.0, 45.0),
    "ab_prime": (0.0, 135.0),
    "a_prime_b": (90.0, 45.0),
    "a_prime_b_prime": (90.0, 135.0),
}
SHOTS = 1024

service = QiskitRuntimeService(channel="ibm_quantum_platform")
backends = [b for b in service.backends(operational=True, simulator=False)]
backend = min(backends, key=lambda b: b.status().pending_jobs)
print(f"backend: {backend.name} ({backend.num_qubits} qubits)", flush=True)

circuits = []
for name, (angle_a, angle_b) in SETTINGS.items():
    qc = QuantumCircuit(2, name=name)
    qc.h(0)
    qc.cx(0, 1)
    qc.ry(math.radians(-angle_a), 0)
    qc.ry(math.radians(-angle_b), 1)
    qc.measure_all()
    circuits.append(qc)

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa = [pm.run(qc) for qc in circuits]
depths = [c.depth() for c in isa]
print(f"depths after transpilation: {depths}", flush=True)

sampler = Sampler(mode=backend)
job = sampler.run(isa, shots=SHOTS)
print(f"job id: {job.job_id()}", flush=True)
result = job.result()

raw = {}
for name, circuit_result in zip(SETTINGS, result):
    raw[name] = {k: int(v) for k, v in circuit_result.data.meas.get_counts().items()}

record = {
    "case": "ibm-chsh",
    "recorded_at": "2026-11-17T00:00:00Z",
    "provider": "ibm_quantum_platform",
    "backend": backend.name,
    "backend_qubits": backend.num_qubits,
    "job_id": job.job_id(),
    "shots": SHOTS,
    "settings": {k: list(v) for k, v in SETTINGS.items()},
    "transpiled_depths": depths,
    "counts": raw,
}
out = ROOT / "runs" / "chapter04/0007-chsh-1024-ibm"
out.mkdir(parents=True, exist_ok=True)
(out / "result.json").write_text(json.dumps(record, indent=2))

print(f"counts: {raw}", flush=True)
print("written", out / "result.json", flush=True)
