"""Grover on three qubits, two iterations, one marked item.

Checks the circuit against the analytic success probability before submitting.
Writes runs/chapter07/0013-grover-3qubits-1024-ibm/result.json.
"""

import json
import pathlib

import numpy as np
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

N = 3
MARKED = 0b101
STEPS = 2
SHOTS = 1024


def multi_z(qc: QuantumCircuit, qubits: list) -> None:
    """Multi-controlled Z: H on the target, multi-controlled X, H back."""
    qc.h(qubits[-1])
    qc.mcx(qubits[:-1], qubits[-1])
    qc.h(qubits[-1])


def oracle_and_diffusion(n: int, marked: int, steps: int) -> QuantumCircuit:
    qc = QuantumCircuit(n, name=f"grover_{marked}_{steps}")
    qc.h(range(n))
    for _ in range(steps):
        # Phase oracle: X around the marked pattern, multi-controlled Z, X back.
        for bit in range(n):
            if not (marked >> (n - 1 - bit)) & 1:
                qc.x(bit)
        multi_z(qc, list(range(n)))
        for bit in range(n):
            if not (marked >> (n - 1 - bit)) & 1:
                qc.x(bit)
        # Diffusion: inversion about the mean.
        qc.h(range(n))
        qc.x(range(n))
        multi_z(qc, list(range(n)))
        qc.x(range(n))
        qc.h(range(n))
    return qc


service = QiskitRuntimeService(channel="ibm_quantum_platform")
backend = min(
    [b for b in service.backends(operational=True, simulator=False)],
    key=lambda b: b.status().pending_jobs,
)
print(f"backend: {backend.name}", flush=True)

circuit = oracle_and_diffusion(N, MARKED, STEPS)
ideal = Statevector.from_instruction(circuit)
probabilities = ideal.probabilities()
expected = float(probabilities[MARKED])
print(f"ideal probability of the marked item: {expected:.4f}", flush=True)
if expected < 0.9:
    raise SystemExit(f"the circuit does not concentrate on the marked item: {expected:.4f}")

measured = circuit.copy()
measured.measure_all()
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa = pm.run(measured)
print(f"depth after transpilation: {isa.depth()}", flush=True)

job = Sampler(mode=backend).run([isa], shots=SHOTS)
print(f"job id: {job.job_id()}", flush=True)
counts = {k: int(v) for k, v in job.result()[0].data.meas.get_counts().items()}

record = {
    "case": "ibm-grover",
    "recorded_at": "2026-11-17T00:00:00Z",
    "provider": "ibm_quantum_platform",
    "backend": backend.name,
    "job_id": job.job_id(),
    "n": N,
    "marked": MARKED,
    "marked_bits": format(MARKED, f"0{N}b"),
    "steps": STEPS,
    "shots": SHOTS,
    "transpiled_depth": isa.depth(),
    "ideal_probability": expected,
    "counts": counts,
}
out = ROOT / "runs" / "chapter07/0013-grover-3qubits-1024-ibm"
out.mkdir(parents=True, exist_ok=True)
(out / "result.json").write_text(json.dumps(record, indent=2))
print(json.dumps(dict(sorted(counts.items(), key=lambda kv: -kv[1])), indent=1), flush=True)
print("written", out / "result.json", flush=True)
