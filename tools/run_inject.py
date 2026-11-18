"""Submit the chapter 17 injection test: does the feed-forward actually correct?

Run: python3 tools/run_inject.py

One X on a data qubit before the syndrome, with and without the conditional
correction. If the mechanism works, the corrected circuit turns the flipped
codeword back and the control does not.

The job is separate from the memory run because it answers a different question:
that run measures whether correction pays, this one measures whether it works.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/0032-ibm-fez-inject"
SHOTS = 4096
FLIPS = (0, 1, 2)


def build(flip: int, correct: bool) -> QuantumCircuit:
    data = QuantumRegister(3, "d")
    ancilla = QuantumRegister(2, "a")
    syn = ClassicalRegister(2, "s")
    out = ClassicalRegister(3, "c")
    qc = QuantumCircuit(data, ancilla, syn, out)
    qc.x(data[flip])
    qc.cx(data[0], ancilla[0])
    qc.cx(data[1], ancilla[0])
    qc.cx(data[1], ancilla[1])
    qc.cx(data[2], ancilla[1])
    qc.measure(ancilla[0], syn[0])
    qc.measure(ancilla[1], syn[1])
    if correct:
        with qc.if_test((syn, 1)):
            qc.x(data[0])
        with qc.if_test((syn, 3)):
            qc.x(data[1])
        with qc.if_test((syn, 2)):
            qc.x(data[2])
    qc.measure(data, out)
    return qc


def main() -> int:
    load_dotenv(ROOT / ".env")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService(channel=os.getenv("QISKIT_IBM_CHANNEL") or "ibm_quantum_platform")
    usage = service.usage()
    print(f"runtime remaining: {usage['usage_remaining_seconds']} s")
    backend = min(service.backends(operational=True, simulator=False), key=lambda b: b.status().pending_jobs)
    print(f"backend {backend.name}, pending {backend.status().pending_jobs}")

    plan = [(flip, correct) for flip in FLIPS for correct in (True, False)]
    circuits = [transpile(build(flip, correct), backend=backend, optimization_level=1) for flip, correct in plan]
    print(f"{len(circuits)} circuits, max depth {max(c.depth() for c in circuits)}")

    sampler = SamplerV2(mode=backend)
    job = sampler.run(circuits, shots=SHOTS)
    print(f"job {job.job_id()} submitted")
    while str(job.status()) not in ("DONE", "JobStatus.DONE"):
        if str(job.status()) in ("ERROR", "CANCELLED", "JobStatus.ERROR", "JobStatus.CANCELLED"):
            raise SystemExit(f"job ended {job.status()}")
        time.sleep(15)

    result = job.result()
    rows = []
    for index, (flip, correct) in enumerate(plan):
        counts = result[index].data.c.get_counts()
        rows.append({"flip": flip, "corrected": correct,
                     "counts": {str(k): int(v) for k, v in counts.items()}})

    record = {
        "case": "ibm-fez-inject",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "ibm_quantum_platform",
        "backend": backend.name,
        "job_id": job.job_id(),
        "shots": SHOTS,
        "flips": list(FLIPS),
        "transpiled_depth": max(c.depth() for c in circuits),
        "results": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(record, indent=2) + "\n")

    for row in rows:
        total = sum(row["counts"].values())
        single = sum(count for key, count in row["counts"].items()
                     if sum(1 for c in key if c == "1") == 1) / total
        clean = row["counts"].get("000", 0) / total
        print(f"flip={row['flip']} corrected={row['corrected']}: clean 000 {clean:.3f}, single flip {single:.3f}")
    print(f"wrote {OUT / 'result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
