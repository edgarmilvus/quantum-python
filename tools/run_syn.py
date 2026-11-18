"""One job with both registers returned: what syndrome does a clean codeword produce?

Run: python3 tools/run_syn.py
"""
from __future__ import annotations
import json, os, time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/0034-ibm-fez-syndrome"
SHOTS = 8192


def build(prepared: int) -> QuantumCircuit:
    d, a = QuantumRegister(3, "d"), QuantumRegister(2, "a")
    s, c = ClassicalRegister(2, "s"), ClassicalRegister(3, "c")
    qc = QuantumCircuit(d, a, s, c)
    if prepared:
        for q in d:
            qc.x(q)
    qc.cx(d[0], a[0]); qc.cx(d[1], a[0]); qc.cx(d[1], a[1]); qc.cx(d[2], a[1])
    qc.measure(a[0], s[0]); qc.measure(a[1], s[1])
    qc.measure(d, c)
    return qc


def main() -> int:
    load_dotenv(ROOT / ".env")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    service = QiskitRuntimeService(channel=os.getenv("QISKIT_IBM_CHANNEL") or "ibm_quantum_platform")
    backend = min(service.backends(operational=True, simulator=False), key=lambda b: b.status().pending_jobs)
    print(f"backend {backend.name}, runtime {service.usage()['usage_remaining_seconds']} s")
    circuits = [transpile(build(p), backend=backend, optimization_level=1) for p in (0, 1)]
    job = SamplerV2(mode=backend).run(circuits, shots=SHOTS)
    print(f"job {job.job_id()}")
    while str(job.status()) not in ("DONE", "JobStatus.DONE"):
        if "ERROR" in str(job.status()):
            raise SystemExit("job failed")
        time.sleep(15)
    res = job.result()
    rows = []
    for index, prepared in enumerate((0, 1)):
        syn = res[index].data.s.get_counts()
        data = res[index].data.c.get_counts()
        rows.append({"prepared": prepared, "syndromes": {str(k): int(v) for k, v in syn.items()},
                     "counts": {str(k): int(v) for k, v in data.items()}})
        total = sum(syn.values())
        print(f"prep {prepared}: syndromes " + ", ".join(f"{k}:{v/total:.3f}" for k, v in sorted(syn.items(), key=lambda kv: -kv[1])))
    record = {"case": "ibm-fez-syndrome", "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "provider": "ibm_quantum_platform", "backend": backend.name, "job_id": job.job_id(),
              "shots": SHOTS, "results": rows}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"wrote {OUT / 'result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
