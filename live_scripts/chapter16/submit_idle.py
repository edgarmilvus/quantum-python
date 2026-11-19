"""Submit the chapter 16 idle-time experiment to ibm_fez, once, and record it.

The same repetition code, held idle for a chosen time before the measurement. Idle
time is where T1 and T2 act, so the logical error grows with it, and the question
is whether a larger distance buys time or only qubits.

Run: python3 live_scripts/chapter16/submit_idle.py
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
OUT = ROOT / "runs/chapter16/0029-idle-0-20-60us-4096-ibm"
SHOTS = 4096
DISTANCES = (3, 5)
PREPARATIONS = (0, 1)
IDLE_US = (0.0, 20.0, 60.0)


def circuit(distance: int, prepared: int, idle: float) -> QuantumCircuit:
    qc = QuantumCircuit(distance)
    if prepared == 1:
        for qubit in range(distance):
            qc.x(qubit)
    if idle > 0:
        for qubit in range(distance):
            qc.delay(idle, qubit, unit="us")
    qc.measure_all()
    return qc


def main() -> int:
    load_dotenv(ROOT / ".env")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService(channel=os.getenv("QISKIT_IBM_CHANNEL") or "ibm_quantum_platform")
    usage = service.usage()
    print(f"runtime remaining: {usage['usage_remaining_seconds']} s")
    backend = min(service.backends(operational=True, simulator=False), key=lambda b: b.status().pending_jobs)
    print(f"backend {backend.name}, pending {backend.status().pending_jobs}, dt {backend.dt}")

    plan = [(d, p, i) for d in DISTANCES for p in PREPARATIONS for i in IDLE_US]
    circuits = [transpile(circuit(d, p, i), backend=backend, optimization_level=1) for d, p, i in plan]
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
    for index, (d, p, i) in enumerate(plan):
        counts = result[index].data.meas.get_counts()
        rows.append({"distance": d, "prepared": p, "idle_us": i,
                     "counts": {str(k): int(v) for k, v in counts.items()}})

    record = {
        "case": "ibm-fez-idle",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "ibm_quantum_platform",
        "backend": backend.name,
        "job_id": job.job_id(),
        "shots": SHOTS,
        "distances": list(DISTANCES),
        "preparations": list(PREPARATIONS),
        "idle_us": list(IDLE_US),
        "transpiled_depth": max(c.depth() for c in circuits),
        "results": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(record, indent=2) + "\n")

    for row in rows:
        total = sum(row["counts"].values())
        flips = 0.0
        wrong = 0
        for key, count in row["counts"].items():
            bits = [int(character) for character in key[::-1]]
            flips += sum(1 for value in bits if value != row["prepared"]) * count
            if (sum(bits) * 2 > row["distance"]) != row["prepared"]:
                wrong += count
        print(f"d={row['distance']} prep={row['prepared']} idle={row['idle_us']}us: "
              f"physical {flips / (total * row['distance']):.4f} logical {wrong / total:.4f}")
    print(f"wrote {OUT / 'result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
