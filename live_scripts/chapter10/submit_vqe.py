"""VQE's converged circuit on a device: two tallies, one energy.

Checks the circuit against the exact value before submitting.
Writes runs/chapter10/0017-vqe-h2-10000-ibm/result.json
"""

import json
import math
import pathlib

import numpy as np
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

THETA = -0.2235
SHOTS = 10_000
EXACT = -1.137305

service = QiskitRuntimeService(channel="ibm_quantum_platform")
backend = min(
    [b for b in service.backends(operational=True, simulator=False)],
    key=lambda b: b.status().pending_jobs,
)
print(f"backend: {backend.name}", flush=True)


def circuit(basis: str) -> QuantumCircuit:
    qc = QuantumCircuit(2, 2)
    qc.x(0)
    qc.ry(THETA, 1)
    qc.cx(1, 0)
    if basis == "X":
        qc.h(0)
        qc.h(1)
    qc.measure([0, 1], [0, 1])
    return qc


z_circuit, x_circuit = circuit("Z"), circuit("X")
for name, qc in (("Z", z_circuit), ("X", x_circuit)):
    ideal = Statevector.from_instruction(qc.remove_final_measurements(inplace=False))
    probs = ideal.probabilities_dict()
    print(f"{name} basis ideal distribution: { {k: round(v, 4) for k, v in probs.items()} }", flush=True)

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa = [pm.run(z_circuit), pm.run(x_circuit)]
print(f"depths: {[c.depth() for c in isa]}", flush=True)

job = Sampler(mode=backend).run(isa, shots=SHOTS)
print(f"job id: {job.job_id()}", flush=True)
result = job.result()

counts = {
    "Z": {k: int(v) for k, v in result[0].data.c.get_counts().items()},
    "X": {k: int(v) for k, v in result[1].data.c.get_counts().items()},
}

record = {
    "case": "ibm-vqe-h2",
    "recorded_at": "2026-11-17T00:00:00Z",
    "provider": "ibm_quantum_platform",
    "backend": backend.name,
    "job_id": job.job_id(),
    "theta": THETA,
    "shots": SHOTS,
    "exact_energy": EXACT,
    "depths": [c.depth() for c in isa],
    "counts": counts,
}
out = ROOT / "runs" / "chapter10/0017-vqe-h2-10000-ibm"
out.mkdir(parents=True, exist_ok=True)
(out / "result.json").write_text(json.dumps(record, indent=2))
print(json.dumps(counts, indent=1), flush=True)
print("written", out / "result.json", flush=True)
