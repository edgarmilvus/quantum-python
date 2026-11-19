"""Submit the chapter 20 teleportation experiment to ibm_fez, once, and record it.

Thirteen circuits in one job: three tomography bases for the dynamic circuit, three for
the postselected one, three for the uncorrected control, and four calibration circuits.
The prepared state is theta = pi/3, phi = pi/4, whose Bloch vector has all three
components non-zero, so the tomography cannot pass by accident.

Run: python3 live_scripts/chapter20/submit_teleport.py
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from qiskit import transpile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/chapter20/0042-teleport-pi3-pi4-2048-ibm"
SHOTS = 2048
THETA = 3.141592653589793 / 3
PHI = 3.141592653589793 / 4

import sys

sys.path.insert(0, str(ROOT / "chapters/chapter20/files"))

from teleport import BASES, Prepared, calibration, teleport  # noqa: E402


def main() -> int:
    load_dotenv(ROOT / ".env")
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService(channel=os.getenv("QISKIT_IBM_CHANNEL") or "ibm_quantum_platform")
    usage = service.usage()
    print(f"runtime remaining: {usage['usage_remaining_seconds']} s")
    backend = min(
        (b for b in service.backends(operational=True, simulator=False)),
        key=lambda b: b.status().pending_jobs,
    )
    print(f"backend {backend.name}, pending {backend.status().pending_jobs}")

    prepared = Prepared(THETA, PHI)
    circuits = []
    plan = []
    for kind, dynamic, correct in (("dynamic", True, True), ("postselect", False, True), ("uncorrected", False, False)):
        for basis in BASES:
            circuits.append(teleport(prepared, basis, dynamic, correct))
            plan.append((kind, basis))
    calibration_circuits = calibration()
    circuits += calibration_circuits
    plan += [("calibration", str(index)) for index in range(len(calibration_circuits))]

    isa = [transpile(circuit, backend=backend, optimization_level=1) for circuit in circuits]
    depth = max(circuit.depth() for circuit in isa)
    print(f"{len(isa)} circuits, max depth {depth}")

    job = SamplerV2(mode=backend).run(isa, shots=SHOTS)
    print(f"job {job.job_id()} submitted")
    while str(job.status()) not in ("DONE", "JobStatus.DONE"):
        if str(job.status()) in ("ERROR", "CANCELLED", "JobStatus.ERROR", "JobStatus.CANCELLED"):
            raise SystemExit(f"job ended {job.status()}")
        time.sleep(10)

    result = job.result()
    record: dict = {
        "case": "ibm-fez-teleport",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": "ibm_quantum_platform",
        "backend": backend.name,
        "job_id": job.job_id(),
        "shots": SHOTS,
        "prepared": {"theta": THETA, "phi": PHI},
        "transpiled_depth": depth,
        "dynamic": {"counts": {}},
        "postselect": {"counts": {}},
        "uncorrected": {"counts": {}},
        "calibration": [],
    }
    for index, (kind, label) in enumerate(plan):
        counts = result[index].data.c.get_counts()
        counts = {str(key): int(value) for key, value in counts.items()}
        if kind == "calibration":
            record["calibration"].append({"prepared": int(label), "counts": counts})
        else:
            record[kind]["counts"][label] = counts

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"wrote {OUT / 'result.json'}")

    from teleport import run

    for kind in ("dynamic", "postselect", "uncorrected"):
        print(run(record, kind).report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
