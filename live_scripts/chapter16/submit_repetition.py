"""Submit the chapter 16 repetition-code memory to ibm_fez, once, and record it.

Three distances and two preparations, at three depths, where a depth is a pair of
logical X layers: an even number returns the codeword, so the only thing a depth
adds is gate error. The measurement is the codeword, and the majority vote is the
decoding.

Run: python3 live_scripts/chapter16/submit_repetition.py
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/chapter16/0028-repetition-d3-d5-4096-ibm"
SHOTS = 4096
DISTANCES = (3, 5)
PREPARATIONS = (0, 1)
DEPTHS = (0, 2, 4)


def circuit(distance: int, prepared: int, layers: int) -> QuantumCircuit:
    qc = QuantumCircuit(distance)
    if prepared == 1:
        for qubit in range(distance):
            qc.x(qubit)
    for _ in range(layers):
        for qubit in range(distance):
            qc.x(qubit)
    qc.measure_all()
    return qc


def main() -> int:
    load_dotenv(ROOT / ".env")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService(channel=os.getenv("QISKIT_IBM_CHANNEL") or "ibm_quantum_platform")
    usage = service.usage()
    print(f"runtime remaining: {usage['usage_remaining_seconds']} s")
    backend = min(service.backends(operational=True, simulator=False), key=lambda b: b.status().pending_jobs)
    print(f"backend {backend.name}, pending {backend.status().pending_jobs}")

    plan = [(d, p, l) for d in DISTANCES for p in PREPARATIONS for l in DEPTHS]
    circuits = [transpile(circuit(d, p, l), backend=backend, optimization_level=1) for d, p, l in plan]
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
    for index, (d, p, l) in enumerate(plan):
        counts = result[index].data.meas.get_counts()
        rows.append({"distance": d, "prepared": p, "layers": l,
                     "counts": {str(k): int(v) for k, v in counts.items()}})

    record = {
        "case": "ibm-fez-repetition",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "ibm_quantum_platform",
        "backend": backend.name,
        "job_id": job.job_id(),
        "shots": SHOTS,
        "distances": list(DISTANCES),
        "preparations": list(PREPARATIONS),
        "depths": list(DEPTHS),
        "transpiled_depth": max(c.depth() for c in circuits),
        "results": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(record, indent=2) + "\n")

    for row in rows:
        total = sum(row["counts"].values())
        bits_rows = []
        for key, count in row["counts"].items():
            bits = [int(c) for c in key[::-1]]
            bits_rows.append((bits, count))
        flips = sum(sum(1 for b in bits if b != row["prepared"]) * count for bits, count in bits_rows) / (total * row["distance"])
        wrong = sum(count for bits, count in bits_rows
                    if (sum(bits) * 2 > row["distance"]) != row["prepared"]) / total
        print(f"d={row['distance']} prep={row['prepared']} layers={row['layers']}: "
              f"physical {flips:.4f} logical {wrong:.4f}")
    print(f"wrote {OUT / 'result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
