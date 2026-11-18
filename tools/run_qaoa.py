"""Submit the chapter 13 QAOA landscape to ibm_fez, once, and record it.

The optimiser needs hundreds of evaluations; a device cannot afford them. So the
hardware experiment is not the optimisation, it is a slice of the landscape: 36
angle pairs on a grid, one job, 1,024 shots each. The chapter then asks whether
the slice the device returned has the same shape as the simulated one.

Run: python3 tools/run_qaoa.py
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/0022-ibm-fez-qaoa"

GRAPH = {"n": 4, "edges": [[0, 1, 1.0], [1, 2, 1.0], [2, 3, 1.0], [3, 0, 1.0], [0, 2, 1.0]]}
SHOTS = 1024
STEPS = 6
BETAS = np.linspace(0.0, np.pi / 2, STEPS)
GAMMAS = np.linspace(0.0, np.pi, STEPS)


def circuit(beta: float, gamma: float) -> QuantumCircuit:
    qc = QuantumCircuit(4)
    for wire in range(4):
        qc.h(wire)
    for i, j, weight in GRAPH["edges"]:
        qc.rzz(-gamma * weight, i, j)
    for wire in range(4):
        qc.rx(2 * beta, wire)
    qc.measure_all()
    return qc


def main() -> int:
    load_dotenv(ROOT / ".env")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService(channel=os.getenv("QISKIT_IBM_CHANNEL") or "ibm_quantum_platform")
    usage = service.usage()
    print(f"runtime remaining: {usage['usage_remaining_seconds']} s")
    backend = min(
        service.backends(operational=True, simulator=False),
        key=lambda b: b.status().pending_jobs,
    )
    print(f"backend {backend.name}, pending {backend.status().pending_jobs}")

    points = [(float(beta), float(gamma)) for beta in BETAS for gamma in GAMMAS]
    circuits = [transpile(circuit(beta, gamma), backend=backend, optimization_level=1) for beta, gamma in points]
    depth = max(item.depth() for item in circuits)
    print(f"{len(circuits)} circuits, max depth {depth}")

    sampler = SamplerV2(mode=backend)
    job = sampler.run(circuits, shots=SHOTS)
    print(f"job {job.job_id()} submitted")
    while True:
        status = job.status()
        if str(status) in ("DONE", "JobStatus.DONE"):
            break
        if str(status) in ("ERROR", "CANCELLED", "JobStatus.ERROR", "JobStatus.CANCELLED"):
            raise SystemExit(f"job ended {status}")
        print(f"  {status} at {datetime.now(timezone.utc).strftime('%H:%M:%S')}")
        time.sleep(20)

    result = job.result()
    rows = []
    for index, (beta, gamma) in enumerate(points):
        counts = result[index].data.meas.get_counts()
        rows.append({"beta": beta, "gamma": gamma, "counts": {str(k): int(v) for k, v in counts.items()}})

    record = {
        "case": "ibm-fez-qaoa-grid",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "ibm_quantum_platform",
        "backend": backend.name,
        "job_id": job.job_id(),
        "shots": SHOTS,
        "graph": GRAPH,
        "grid": {"beta": [float(x) for x in BETAS], "gamma": [float(x) for x in GAMMAS]},
        "transpiled_depth": depth,
        "runtime_seconds_before": usage.get("usage_consumed_seconds"),
        "results": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(record, indent=2) + "\n")

    # The headline, computed the way the chapter computes it.
    optimum = 4.0
    best = max(rows, key=lambda row: mean_cut(row["counts"]))
    print(f"best measured point: beta {best['beta']:.4f} gamma {best['gamma']:.4f}")
    print(f"  mean cut {mean_cut(best['counts']):.4f} of an optimum {optimum}")
    usage_after = service.usage()
    print(f"runtime remaining after: {usage_after['usage_remaining_seconds']} s")
    print(f"wrote {OUT / 'result.json'}")
    return 0


def mean_cut(counts: dict) -> float:
    total = sum(counts.values())
    edges = GRAPH["edges"]
    value = 0.0
    for key, count in counts.items():
        bits = int(key, 2)
        value += sum(weight for i, j, weight in edges if ((bits >> i) & 1) != ((bits >> j) & 1)) * count
    return value / total


if __name__ == "__main__":
    raise SystemExit(main())
