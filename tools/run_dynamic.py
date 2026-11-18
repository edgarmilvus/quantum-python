"""Submit the chapter 17 dynamic-circuit experiment to ibm_fez, once, and record it.

A three-qubit repetition code with in-circuit syndrome extraction and a conditional
correction. Two preparations, two idle times, and a control without the correction,
so the run measures what feed-forward buys rather than asserting it.

Run: python3 tools/run_dynamic.py
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
OUT = ROOT / "runs/0031-ibm-fez-dynamic"
SHOTS = 4096
PREPARATIONS = (0, 1)
IDLES = (0.0, 20.0)
CORRECTIONS = (True, False)


def build(prepared: int, idle: float, correct: bool) -> QuantumCircuit:
    data = QuantumRegister(3, "d")
    ancilla = QuantumRegister(2, "a")
    syn = ClassicalRegister(2, "s")
    out = ClassicalRegister(3, "c")
    qc = QuantumCircuit(data, ancilla, syn, out)
    if prepared == 1:
        for qubit in data:
            qc.x(qubit)
    if idle > 0:
        for qubit in data:
            qc.delay(idle, qubit, unit="us")
    # syndrome extraction: s0 = d0 ^ d1, s1 = d1 ^ d2
    qc.cx(data[0], ancilla[0])
    qc.cx(data[1], ancilla[0])
    qc.cx(data[1], ancilla[1])
    qc.cx(data[2], ancilla[1])
    qc.measure(ancilla[0], syn[0])
    qc.measure(ancilla[1], syn[1])
    if correct:
        # The runtime refuses nested control flow (error 1524), so the three
        # syndromes are one register compared with three constants.
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

    plan = [(p, i, c) for p in PREPARATIONS for i in IDLES for c in CORRECTIONS]
    circuits = []
    for prepared, idle, correct in plan:
        raw = build(prepared, idle, correct)
        circuits.append(transpile(raw, backend=backend, optimization_level=1))
    print(f"{len(circuits)} circuits, max depth {max(c.depth() for c in circuits)}")
    ops = circuits[0].count_ops()
    print(f"first circuit ops: {dict(ops)}")

    sampler = SamplerV2(mode=backend)
    job = sampler.run(circuits, shots=SHOTS)
    print(f"job {job.job_id()} submitted")
    while str(job.status()) not in ("DONE", "JobStatus.DONE"):
        if str(job.status()) in ("ERROR", "CANCELLED", "JobStatus.ERROR", "JobStatus.CANCELLED"):
            raise SystemExit(f"job ended {job.status()}")
        time.sleep(15)

    result = job.result()
    rows = []
    for index, (prepared, idle, correct) in enumerate(plan):
        data = result[index].data
        counts = data.c.get_counts()
        rows.append({"prepared": prepared, "idle_us": idle, "corrected": correct,
                     "counts": {str(k): int(v) for k, v in counts.items()}})

    record = {
        "case": "ibm-fez-dynamic",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "ibm_quantum_platform",
        "backend": backend.name,
        "job_id": job.job_id(),
        "shots": SHOTS,
        "preparations": list(PREPARATIONS),
        "idle_us": list(IDLES),
        "corrections": list(CORRECTIONS),
        "transpiled_depth": max(c.depth() for c in circuits),
        "results": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(record, indent=2) + "\n")

    for row in rows:
        total = sum(row["counts"].values())
        wrong = 0
        for key, count in row["counts"].items():
            bits = [int(c) for c in key[::-1]]
            if (sum(bits) * 2 > 3) != row["prepared"]:
                wrong += count
        print(f"prep={row['prepared']} idle={row['idle_us']}us corrected={row['corrected']}: "
              f"logical {wrong / total:.4f}")
    print(f"wrote {OUT / 'result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
