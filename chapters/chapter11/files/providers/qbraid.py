"""qBraid over its REST API: the aggregator, as a seventh adapter.

qBraid is not a provider of machines. It is a gateway in front of IBM, IonQ, IQM,
Rigetti, QuEra, Pasqal and others, and its value to this book is that one key and
one job schema reach all of them. The adapter is short because the schema is:
submit a program with a format and a body, poll the job QRN, fetch the result.

The free tier's simulators cost no credits, which is why this is the adapter the
chapter can run live on any machine with an account.
"""

from __future__ import annotations

import os
import time
from typing import Dict, List, Optional

import requests

from .base import Backend, BackendError, Circuit, Job, Profile, Result

BASE = "https://api-v2.qbraid.com/api/v1"

# QASM 2 has no sx and no arbitrary two-qubit rotation, so the gates the book
# uses map onto this table and anything else is refused rather than dropped.
SINGLE = {"h": "h", "x": "x", "y": "y", "z": "z", "s": "s", "t": "t"}
ROTATION = {"rx": "rx", "ry": "ry", "rz": "rz"}
TWO = {"cx": "cx", "cnot": "cx", "cz": "cz"}


def to_qasm(circuit: Circuit, name: str = "book") -> str:
    """The chapter's circuit as an OPENQASM 2 program, measured at the end."""
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', f"qreg q[{circuit.wires}];", f"creg c[{circuit.wires}];"]
    for gate, wires, theta in circuit.ops:
        if gate in TWO:
            if len(wires) != 2:
                raise BackendError(f"{gate} needs two wires, got {wires}")
            lines.append(f"{TWO[gate]} q[{wires[0]}],q[{wires[1]}];")
        elif gate in ROTATION:
            if theta is None:
                raise BackendError(f"{gate} needs an angle")
            lines.append(f"{ROTATION[gate]}({float(theta):.10f}) q[{wires[0]}];")
        elif gate in SINGLE:
            lines.append(f"{SINGLE[gate]} q[{wires[0]}];")
        else:
            raise BackendError(f"qBraid adapter does not translate {gate!r} to QASM 2")
    lines.append("measure q -> c;")
    return "\n".join(lines) + "\n"


class Qbraid(Backend):
    provider = "qbraid"

    def __init__(
        self,
        device: str = "qbraid:qbraid:sim:qir-sv",
        token: Optional[str] = None,
        timeout: float = 300.0,
    ) -> None:
        self.name = device
        self._device = device
        self._token = token or os.getenv("QBRAID_API_KEY", "")
        if not self._token:
            raise BackendError("QBRAID_API_KEY is not set; use Replay or set the key")
        self._timeout = timeout

    @property
    def headers(self) -> Dict[str, str]:
        return {"X-API-Key": self._token, "Content-Type": "application/json"}

    # -- the four operations ---------------------------------------------
    def profile(self) -> Profile:
        response = requests.get(f"{BASE}/devices", headers=self.headers, timeout=30)
        if response.status_code != 200:
            raise BackendError(f"qBraid devices returned HTTP {response.status_code}")
        for entry in response.json().get("data", []):
            if entry.get("qrn") == self._device:
                return Profile(
                    provider=self.provider,
                    backend=self._device,
                    qubits=int(entry.get("numberQubits") or 0),
                    basis=("h", "x", "y", "z", "s", "t", "rx", "ry", "rz", "cx", "cz"),
                    queue=0,
                )
        raise BackendError(f"qBraid has no device {self._device!r}")

    def submit(self, circuit: Circuit, shots: int) -> Job:
        self.check_shots(shots)
        payload = {
            "name": "quantum-python",
            "shots": shots,
            "deviceQrn": self._device,
            "program": {"format": "qasm2", "data": to_qasm(circuit)},
        }
        response = requests.post(f"{BASE}/jobs", headers=self.headers, json=payload, timeout=60)
        if response.status_code not in (200, 201):
            raise BackendError(f"qBraid submit returned HTTP {response.status_code}: {response.text[:200]}")
        created = response.json().get("data", {})
        return Job(
            provider=self.provider,
            backend=self._device,
            id=str(created["jobQrn"]),
            shots=shots,
            depth=circuit.depth(),
        )

    def status(self, job: Job) -> str:
        response = requests.get(f"{BASE}/jobs/{job.id}", headers=self.headers, timeout=30)
        if response.status_code != 200:
            raise BackendError(f"qBraid status returned HTTP {response.status_code}")
        return str(response.json().get("data", {}).get("status", "unknown"))

    def result(self, job: Job) -> Result:
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            response = requests.get(f"{BASE}/jobs/{job.id}", headers=self.headers, timeout=30)
            if response.status_code != 200:
                raise BackendError(f"qBraid status returned HTTP {response.status_code}")
            status = str(response.json().get("data", {}).get("status", "unknown"))
            if status == "COMPLETED":
                return self._fetch(job)
            if status in ("FAILED", "CANCELLED", "ERROR"):
                raise BackendError(f"qBraid job {job.id} ended {status}")
            time.sleep(2)
        raise BackendError(f"qBraid job {job.id} did not finish within {self._timeout:.0f} s")

    def cancel(self, job: Job) -> None:
        # The v2 API exposes cancellation through the SDK; the REST surface the
        # chapter uses does not, and the interface allows this to be unimplemented.
        raise BackendError(f"{self.provider} cancels through its SDK, not this endpoint")

    # -- the translation this adapter owns -------------------------------
    def _fetch(self, job: Job) -> Result:
        response = requests.get(f"{BASE}/jobs/{job.id}/result", headers=self.headers, timeout=30)
        if response.status_code != 200:
            raise BackendError(f"qBraid result returned HTTP {response.status_code}")
        data = response.json().get("data", {})
        counts = data.get("resultData", {}).get("measurementCounts")
        if not counts:
            raise BackendError(f"qBraid job {job.id} has no counts")
        return Result(job=job, counts={str(key): int(value) for key, value in counts.items()})
