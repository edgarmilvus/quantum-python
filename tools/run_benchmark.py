"""Submit the chapter 18 benchmark circuit to IBM and to qBraid, once each.

The task is a three-qubit GHZ state: H, CX, CX, measure. The ideal distribution is
000 and 111 at one half each, so a single number — the total variation distance
from the ideal — says how far a backend is, and the same number is comparable
across providers that share nothing but the circuit.

Run: python3 tools/run_benchmark.py
"""

from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile

ROOT = Path(__file__).resolve().parents[1]
SHOTS = 4096
IDEAL = {"000": 0.5, "111": 0.5}


def ghz(delay_us: float = 0.0) -> QuantumCircuit:
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    if delay_us > 0:
        for qubit in range(3):
            qc.delay(delay_us, qubit, unit="us")
    qc.measure_all()
    return qc


def total_variation(counts: dict, ideal: dict = IDEAL) -> float:
    total = sum(counts.values())
    keys = set(counts) | set(ideal)
    observed = {key: counts.get(key, 0) / total for key in keys}
    return 0.5 * sum(abs(observed[key] - ideal.get(key, 0.0)) for key in keys)


def run_ibm() -> dict:
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService(channel=os.getenv("QISKIT_IBM_CHANNEL") or "ibm_quantum_platform")
    usage = service.usage()
    print(f"ibm: runtime remaining {usage['usage_remaining_seconds']} s")
    backend = min(service.backends(operational=True, simulator=False), key=lambda b: b.status().pending_jobs)
    circuits = [transpile(ghz(0.0), backend=backend, optimization_level=1),
                transpile(ghz(20.0), backend=backend, optimization_level=1)]
    started = time.monotonic()
    job = SamplerV2(mode=backend).run(circuits, shots=SHOTS)
    print(f"ibm: job {job.job_id()} on {backend.name}")
    while str(job.status()) not in ("DONE", "JobStatus.DONE"):
        if str(job.status()) in ("ERROR", "CANCELLED", "JobStatus.ERROR", "JobStatus.CANCELLED"):
            raise SystemExit(f"ibm job ended {job.status()}")
        time.sleep(10)
    elapsed = time.monotonic() - started
    result = job.result()
    rows = []
    for index, delay in enumerate((0.0, 20.0)):
        counts = result[index].data.meas.get_counts()
        rows.append({"delay_us": delay, "counts": {str(k): int(v) for k, v in counts.items()}})
    record = {
        "case": "ibm-fez-ghz",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "ibm_quantum_platform",
        "backend": backend.name,
        "job_id": job.job_id(),
        "shots": SHOTS,
        "circuit": "ghz-3",
        "ideal": IDEAL,
        "wall_seconds": round(elapsed, 1),
        "transpiled_depth": max(c.depth() for c in circuits),
        "results": rows,
    }
    out = ROOT / "runs/0036-ibm-fez-ghz"
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    for row in rows:
        print(f"  ibm delay {row['delay_us']} us: tvd {total_variation(row['counts']):.4f}")
    print(f"ibm: {elapsed:.1f} s wall, wrote {out / 'result.json'}")
    return record


def run_qbraid() -> dict:
    key = os.getenv("QBRAID_API_KEY", "")
    if not key:
        raise SystemExit("QBRAID_API_KEY is not set")
    qasm = (
        'OPENQASM 2.0; include "qelib1.inc"; qreg q[3]; creg c[3]; '
        "h q[0]; cx q[0],q[1]; cx q[1],q[2]; measure q -> c;"
    )
    body = {"name": "quantum-python-ghz", "shots": SHOTS,
            "deviceQrn": "ionq:ionq:sim:simulator",
            "program": {"format": "qasm2", "data": qasm}}
    headers = {"X-API-Key": key, "Content-Type": "application/json"}
    started = time.monotonic()
    created = requests.post("https://api-v2.qbraid.com/api/v1/jobs", headers=headers, json=body, timeout=60)
    if created.status_code not in (200, 201):
        raise SystemExit(f"qbraid submit failed: {created.status_code} {created.text[:200]}")
    job = created.json()["data"]["jobQrn"]
    print(f"qbraid: job {job}")
    while True:
        status = requests.get(f"https://api-v2.qbraid.com/api/v1/jobs/{job}", headers=headers, timeout=30).json()["data"]["status"]
        if status == "COMPLETED":
            break
        if status in ("FAILED", "CANCELLED", "ERROR"):
            raise SystemExit(f"qbraid job ended {status}")
        time.sleep(3)
    result = requests.get(f"https://api-v2.qbraid.com/api/v1/jobs/{job}/result", headers=headers, timeout=30).json()
    counts = result["data"]["resultData"]["measurementCounts"]
    elapsed = time.monotonic() - started
    record = {
        "case": "qbraid-ionq-sim-ghz",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "qbraid",
        "backend": "ionq:ionq:sim:simulator",
        "job_id": job,
        "shots": SHOTS,
        "circuit": "ghz-3",
        "ideal": IDEAL,
        "wall_seconds": round(elapsed, 1),
        "cost_credits": result["data"].get("cost", "0"),
        "results": [{"delay_us": 0.0, "counts": {str(k): int(v) for k, v in counts.items()}}],
    }
    out = ROOT / "runs/0037-qbraid-ghz"
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"  qbraid: tvd {total_variation(counts):.4f}, {elapsed:.1f} s wall")
    print(f"qbraid: wrote {out / 'result.json'}")
    return record


if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    run_ibm()
    run_qbraid()
