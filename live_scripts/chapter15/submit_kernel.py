"""Submit the chapter 15 kernel matrix to ibm_fez, once, and record it.

The matrix needs 21 distinct training pairs and 36 train-test pairs, so one job of
57 circuits. Each circuit prepares U(x), applies U(x')-dagger, and measures; the
all-zero frequency estimates |<x'|x>|^2.

Run: python3 live_scripts/chapter15/submit_kernel.py
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/chapter15/0026-kernel-12points-57x1024-ibm"
REPS = 3
SHOTS = 1024


def spiral(per_class: int = 6, turns: float = 1.5):
    points = []
    for k in range(per_class):
        angle = turns * 2 * math.pi * k / (per_class - 1)
        radius = 0.08 + 0.30 * k / (per_class - 1)
        points.append((0.5 + radius * math.cos(angle), 0.5 + radius * math.sin(angle)))
        points.append((0.5 - radius * math.cos(angle), 0.5 - radius * math.sin(angle)))
    labels = [1 if i % 2 == 0 else -1 for i in range(len(points))]
    return points, labels


def encode(qc: QuantumCircuit, point, reps: int) -> None:
    """Qiskit's ZZFeatureMap: H once, then reps layers of RZ and RZZ."""
    for wire in range(len(point)):
        qc.h(wire)
    for _ in range(reps):
        for wire, value in enumerate(point):
            qc.rz(2 * value, wire)
        for i in range(len(point)):
            for j in range(i + 1, len(point)):
                phi = (math.pi - point[i]) * (math.pi - point[j])
                qc.rzz(2 * phi, i, j)


def overlap(a, b, reps: int = REPS) -> QuantumCircuit:
    """U(a) followed by U(b)-dagger: all-zero probability is the squared overlap."""
    left = QuantumCircuit(len(a))
    encode(left, a, reps)
    right = QuantumCircuit(len(b))
    encode(right, b, reps)
    qc = left.compose(right.inverse())
    qc.measure_all()
    return qc


def main() -> int:
    load_dotenv(ROOT / ".env")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    points, labels = spiral()
    positives = [i for i, label in enumerate(labels) if label == 1]
    negatives = [i for i, label in enumerate(labels) if label == -1]
    train = positives[:3] + negatives[:3]
    test = positives[3:] + negatives[3:]

    pairs = [(i, j) for index, i in enumerate(train) for j in train[index:]]
    pairs += [(i, j) for i in train for j in test]
    print(f"{len(train)} train, {len(test)} test, {len(pairs)} circuits")

    service = QiskitRuntimeService(channel=os.getenv("QISKIT_IBM_CHANNEL") or "ibm_quantum_platform")
    usage = service.usage()
    print(f"runtime remaining: {usage['usage_remaining_seconds']} s")
    backend = min(service.backends(operational=True, simulator=False), key=lambda b: b.status().pending_jobs)
    print(f"backend {backend.name}, pending {backend.status().pending_jobs}")

    circuits = [transpile(overlap(points[i], points[j]), backend=backend, optimization_level=1) for i, j in pairs]
    depth = max(item.depth() for item in circuits)
    print(f"max depth {depth}")

    sampler = SamplerV2(mode=backend)
    job = sampler.run(circuits, shots=SHOTS)
    print(f"job {job.job_id()} submitted")
    while str(job.status()) not in ("DONE", "JobStatus.DONE"):
        if str(job.status()) in ("ERROR", "CANCELLED", "JobStatus.ERROR", "JobStatus.CANCELLED"):
            raise SystemExit(f"job ended {job.status()}")
        import time

        time.sleep(15)

    result = job.result()
    rows = []
    for index, (i, j) in enumerate(pairs):
        counts = result[index].data.meas.get_counts()
        rows.append({"i": i, "j": j, "counts": {str(k): int(v) for k, v in counts.items()}})

    record = {
        "case": "ibm-fez-kernel-spiral",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "ibm_quantum_platform",
        "backend": backend.name,
        "job_id": job.job_id(),
        "shots": SHOTS,
        "reps": REPS,
        "points": points,
        "labels": labels,
        "train": train,
        "test": test,
        "transpiled_depth": depth,
        "results": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(record, indent=2) + "\n")

    def fidelity(row):
        total = sum(row["counts"].values())
        return sum(v for k, v in row["counts"].items() if set(k) == {"0"}) / total

    diagonal = [fidelity(row) for row in rows if row["i"] == row["j"]]
    print(f"diagonal mean {sum(diagonal) / len(diagonal):.4f} over {len(diagonal)} self-pairs")
    print(f"wrote {OUT / 'result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
