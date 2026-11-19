"""Bernstein-Vazirani with a three-bit secret on a real device.

Writes runs/chapter06/0011-bv-1011-1024-ibm/result.json. One job, one circuit, 1024 shots.
"""

import json
import math
import pathlib

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

SECRET = 0b101
N = 3
SHOTS = 1024

service = QiskitRuntimeService(channel="ibm_quantum_platform")
backend = min(
    [b for b in service.backends(operational=True, simulator=False)],
    key=lambda b: b.status().pending_jobs,
)
print(f"backend: {backend.name}", flush=True)

qc = QuantumCircuit(N + 1, N)
# The output qubit must start at 1 so that H puts it in |->, the state the oracle
# needs to write a phase instead of a bit flip.
qc.x(N)
for qubit in range(N + 1):
    qc.h(qubit)
for bit in range(N):
    if SECRET >> bit & 1:
        qc.cx(bit, N)
for qubit in range(N):
    qc.h(qubit)
qc.measure(range(N), range(N))

ideal = Statevector.from_instruction(qc.remove_final_measurements(inplace=False))
support = list(ideal.probabilities_dict())
print(f"ideal outcomes: {support}", flush=True)
expected = format(SECRET, f"0{N}b")
if not any(key.startswith("0") and key[1:] == expected for key in support):
    raise SystemExit(f"the circuit does not prepare the secret: {support}")

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa = pm.run(qc)
print(f"depth after transpilation: {isa.depth()}", flush=True)

job = Sampler(mode=backend).run([isa], shots=SHOTS)
print(f"job id: {job.job_id()}", flush=True)
result = job.result()
counts = {k: int(v) for k, v in result[0].data.c.get_counts().items()}

record = {
    "case": "ibm-bernstein-vazirani",
    "recorded_at": "2026-11-17T00:00:00Z",
    "provider": "ibm_quantum_platform",
    "backend": backend.name,
    "job_id": job.job_id(),
    "secret": SECRET,
    "secret_bits": format(SECRET, f"0{N}b"),
    "n": N,
    "shots": SHOTS,
    "transpiled_depth": isa.depth(),
    "counts": counts,
}
out = ROOT / "runs" / "chapter06/0011-bv-1011-1024-ibm"
out.mkdir(parents=True, exist_ok=True)
(out / "result.json").write_text(json.dumps(record, indent=2))
print(json.dumps(counts, indent=1), flush=True)
print("written", out / "result.json", flush=True)
