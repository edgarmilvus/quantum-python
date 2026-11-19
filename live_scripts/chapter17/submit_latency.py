"""Submit the chapter 17 latency probe: the conditional with and without its gate.

Run: python3 live_scripts/chapter17/submit_latency.py

Three circuits on a clean |111>: no conditional, a conditional that applies an
identity, and the real correction. The middle one isolates the cost of the
classical round trip from the cost of the correction itself.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/chapter17/0033-latency-conditional-4096-ibm"
SHOTS = 4096
MODES = ("none", "noop", "correct")


def build(mode: str) -> QuantumCircuit:
    data = QuantumRegister(3, "d")
    ancilla = QuantumRegister(2, "a")
    syn = ClassicalRegister(2, "s")
    out = ClassicalRegister(3, "c")
    qc = QuantumCircuit(data, ancilla, syn, out)
    for qubit in data:
        qc.x(qubit)
    qc.cx(data[0], ancilla[0])
    qc.cx(data[1], ancilla[0])
    qc.cx(data[1], ancilla[1])
    qc.cx(data[2], ancilla[1])
    qc.measure(ancilla[0], syn[0])
    qc.measure(ancilla[1], syn[1])
    if mode in ("noop", "correct"):
        with qc.if_test((syn, 1)):
            qc.id(data[0]) if mode == "noop" else qc.x(data[0])
        with qc.if_test((syn, 3)):
            qc.id(data[1]) if mode == "noop" else qc.x(data[1])
        with qc.if_test((syn, 2)):
            qc.id(data[2]) if mode == "noop" else qc.x(data[2])
    qc.measure(data, out)
    return qc


def main() -> int:
    load_dotenv(ROOT / ".env")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService(channel=os.getenv("QISKIT_IBM_CHANNEL") or "ibm_quantum_platform")
    print(f"runtime remaining: {service.usage()['usage_remaining_seconds']} s")
    backend = min(service.backends(operational=True, simulator=False), key=lambda b: b.status().pending_jobs)
    print(f"backend {backend.name}")

    circuits = [transpile(build(mode), backend=backend, optimization_level=1) for mode in MODES]
    for mode, circuit in zip(MODES, circuits):
        print(f"  {mode}: depth {circuit.depth()}, if_else {circuit.count_ops().get('if_else', 0)}")

    sampler = SamplerV2(mode=backend)
    job = sampler.run(circuits, shots=SHOTS)
    print(f"job {job.job_id()} submitted")
    while str(job.status()) not in ("DONE", "JobStatus.DONE"):
        if str(job.status()) in ("ERROR", "CANCELLED", "JobStatus.ERROR", "JobStatus.CANCELLED"):
            raise SystemExit(f"job ended {job.status()}")
        time.sleep(15)

    result = job.result()
    rows = []
    for index, mode in enumerate(MODES):
        counts = result[index].data.c.get_counts()
        rows.append({"mode": mode, "counts": {str(k): int(v) for k, v in counts.items()}})

    record = {
        "case": "ibm-fez-latency",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "ibm_quantum_platform",
        "backend": backend.name,
        "job_id": job.job_id(),
        "shots": SHOTS,
        "modes": list(MODES),
        "transpiled_depth": max(c.depth() for c in circuits),
        "results": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(record, indent=2) + "\n")

    for row in rows:
        total = sum(row["counts"].values())
        clean = row["counts"].get("111", 0) / total
        wrong = sum(count for key, count in row["counts"].items()
                    if (sum(1 for c in key if c == "1") * 2 <= 3)) / total
        print(f"{row['mode']:8s} clean 111 {clean:.4f}  logical error {wrong:.4f}")
    print(f"wrote {OUT / 'result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
