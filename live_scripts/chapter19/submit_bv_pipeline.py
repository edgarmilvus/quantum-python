"""Submit the chapter 19 pipeline experiment to ibm_fez, once, and record it.

One task and one calibration, in a single job: a Bernstein-Vazirani circuit with the
secret 1011 at 2,048 shots, and five circuits that prepare each qubit in |1> plus the
all-zero state, which is what a per-qubit readout model needs.

Run: python3 live_scripts/chapter19/submit_bv_pipeline.py
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from qiskit import ClassicalRegister, QuantumCircuit, transpile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/chapter19/0039-bv-1011-pipeline-2048-ibm"
SHOTS = 2048
SECRET = "1011"


def bv(secret: str) -> QuantumCircuit:
    """Data qubits 0..n-1, one ancilla in |->, and only the data are measured."""
    n = len(secret)
    qc = QuantumCircuit(n + 1)
    qc.x(n)
    for qubit in range(n + 1):
        qc.h(qubit)
    for qubit, bit in enumerate(reversed(secret)):
        if bit == "1":
            qc.cx(qubit, n)
    for qubit in range(n):
        qc.h(qubit)
    creg = ClassicalRegister(n, "c")
    qc.add_register(creg)
    qc.measure(list(range(n)), list(creg))
    return qc


def calibration(n: int) -> list[QuantumCircuit]:
    """All zeros, then one circuit per qubit with that qubit prepared in |1>."""
    circuits = []
    zeros = QuantumCircuit(n)
    zeros.measure_all()
    circuits.append(zeros)
    for qubit in range(n):
        qc = QuantumCircuit(n)
        qc.x(qubit)
        qc.measure_all()
        circuits.append(qc)
    return circuits


def main() -> int:
    load_dotenv(ROOT / ".env")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService(channel=os.getenv("QISKIT_IBM_CHANNEL") or "ibm_quantum_platform")
    usage = service.usage()
    print(f"runtime remaining: {usage['usage_remaining_seconds']} s")
    backend = min(service.backends(operational=True, simulator=False), key=lambda b: b.status().pending_jobs)
    print(f"backend {backend.name}, pending {backend.status().pending_jobs}")

    n = len(SECRET)
    circuits = [bv(SECRET)] + calibration(n)
    isa = [transpile(circuit, backend=backend, optimization_level=1) for circuit in circuits]
    print(f"{len(isa)} circuits, max depth {max(c.depth() for c in isa)}")

    job = SamplerV2(mode=backend).run(isa, shots=SHOTS)
    print(f"job {job.job_id()} submitted")
    while str(job.status()) not in ("DONE", "JobStatus.DONE"):
        if str(job.status()) in ("ERROR", "CANCELLED", "JobStatus.ERROR", "JobStatus.CANCELLED"):
            raise SystemExit(f"job ended {job.status()}")
        time.sleep(10)

    result = job.result()
    task = result[0].data.c.get_counts()
    cal = []
    for index in range(n + 1):
        counts = result[index + 1].data.meas.get_counts()
        cal.append({"prepared": index, "counts": {str(k): int(v) for k, v in counts.items()}})

    record = {
        "case": "ibm-fez-pipeline-bv",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "ibm_quantum_platform",
        "backend": backend.name,
        "job_id": job.job_id(),
        "shots": SHOTS,
        "secret": SECRET,
        "circuit": "bernstein-vazirani",
        "transpiled_depth": max(c.depth() for c in isa),
        "calibration": cal,
        "counts": {str(k): int(v) for k, v in task.items()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(record, indent=2) + "\n")

    top = max(record["counts"], key=record["counts"].get)
    print(f"top outcome {top} with {record['counts'][top] / SHOTS:.3f} of the shots")
    print(f"wrote {OUT / 'result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
