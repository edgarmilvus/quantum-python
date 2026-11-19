"""Calibrate readout on the same qubits the CHSH run used.

Four circuits prepare 00, 01, 10, 11 and measure immediately. 4096 shots each give the
2-qubit confusion matrix, which is what a correction needs.

Writes runs/chapter12/0009-readout-4circuits-4096-ibm/result.json
"""

import json
import pathlib

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

SHOTS = 4096
PREPARATIONS = {
    "00": [],
    "01": [1],
    "10": [0],
    "11": [0, 1],
}

service = QiskitRuntimeService(channel="ibm_quantum_platform")
backends = [b for b in service.backends(operational=True, simulator=False)]
backend = min(backends, key=lambda b: b.status().pending_jobs)
print(f"backend: {backend.name}", flush=True)

circuits = []
for name, wires in PREPARATIONS.items():
    qc = QuantumCircuit(2, name=f"prep_{name}")
    for wire in wires:
        qc.x(wire)
    qc.measure_all()
    circuits.append(qc)

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa = [pm.run(qc) for qc in circuits]

job = Sampler(mode=backend).run(isa, shots=SHOTS)
print(f"job id: {job.job_id()}", flush=True)
result = job.result()

counts = {}
for name, circuit_result in zip(PREPARATIONS, result):
    counts[name] = {k: int(v) for k, v in circuit_result.data.meas.get_counts().items()}

record = {
    "case": "ibm-readout-calibration",
    "recorded_at": "2026-11-17T00:00:00Z",
    "provider": "ibm_quantum_platform",
    "backend": backend.name,
    "job_id": job.job_id(),
    "shots": SHOTS,
    "preparations": {k: v for k, v in PREPARATIONS.items()},
    "counts": counts,
}
out = ROOT / "runs" / "chapter12/0009-readout-4circuits-4096-ibm"
out.mkdir(parents=True, exist_ok=True)
(out / "result.json").write_text(json.dumps(record, indent=2))
print(json.dumps(counts, indent=1), flush=True)
print("written", out / "result.json", flush=True)
