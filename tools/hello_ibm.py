"""Minimal IBM Quantum check: connect, pick the least busy QPU, run a Bell pair.

Costs a few seconds of runtime. Prints raw counts, so the result can be
quoted in the book without interpretation.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv(".env", override=True)

token = os.getenv("QISKIT_IBM_TOKEN", "")
instance = os.getenv("QISKIT_IBM_INSTANCE", "")
if not token or not instance:
    sys.exit("missing QISKIT_IBM_TOKEN or QISKIT_IBM_INSTANCE in .env")
print(f"token: {len(token)} chars | instance: ...{instance[-18:]}", flush=True)

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

service = QiskitRuntimeService(channel="ibm_quantum_platform", instance=instance)
backends = service.backends(operational=True, simulator=False)
if not backends:
    sys.exit("no operational QPU visible for this instance")

for b in backends:
    print(f"  {b.name:26s} {b.num_qubits:3d} qubits  pending={b.status().pending_jobs}", flush=True)

backend = min(backends, key=lambda b: b.status().pending_jobs)
print(f"chosen: {backend.name}", flush=True)

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa = pm.run(qc)
print(f"depth after transpile: {isa.depth()}", flush=True)

job = Sampler(mode=backend).run([isa], shots=1024)
print(f"job id: {job.job_id()}", flush=True)

result = job.result()
counts = result[0].data.meas.get_counts()
total = sum(counts.values())
print(f"counts: {dict(sorted(counts.items()))}", flush=True)
print(f"shots: {total}", flush=True)
for state in ("00", "11"):
    print(f"  P({state}) = {counts.get(state, 0) / total:.3f}", flush=True)
print("correlated:", set(counts) <= {"00", "11"} or "not exactly, see counts", flush=True)
