"""IonQ over its REST API, in about a hundred lines and no SDK.

The simulator is free, so this is the adapter the chapter runs live.
"""

from __future__ import annotations

import os
import time
from typing import Dict, List, Optional

import requests

from .base import Backend, BackendError, Circuit, Job, Profile, Result

BASE = "https://api.ionq.co/v0.3"

GATES = {"h": "h", "x": "x", "y": "y", "z": "z", "s": "s", "t": "t", "sx": "sx"}


def _circuit_body(circuit: Circuit) -> List[Dict]:
    body = []
    for name, wires, theta in circuit.ops:
        if name in ("cx", "cnot"):
            body.append({"gate": "cnot", "control": wires[0], "target": wires[1]})
        elif name in ("rx", "ry", "rz"):
            body.append({"gate": name, "target": wires[0], "rotation": float(theta)})
        elif name in GATES:
            body.append({"gate": GATES[name], "target": wires[0]})
        else:
            raise BackendError(f"IonQ adapter does not translate {name!r}")
    return body


class IonQ(Backend):
    provider = "ionq"

    def __init__(self, target: str = "simulator", token: Optional[str] = None, timeout: float = 120.0) -> None:
        self.name = target
        self._target = target
        self._token = token or os.getenv("IONQ_API_KEY", "")
        if not self._token:
            raise BackendError("IONQ_API_KEY is not set; use Replay or set the key")
        self._timeout = timeout

    @property
    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"apiKey {self._token}", "Content-Type": "application/json"}

    # -- the four operations ---------------------------------------------
    def profile(self) -> Profile:
        response = requests.get(f"{BASE}/backends", headers=self.headers, timeout=30)
        if response.status_code != 200:
            raise BackendError(f"IonQ backends returned HTTP {response.status_code}")
        entries = response.json()
        for entry in entries:
            if entry.get("backend") == self._target:
                return Profile(
                    provider=self.provider,
                    backend=self._target,
                    qubits=int(entry.get("qubits", 0)),
                    basis=("h", "x", "y", "z", "s", "t", "rx", "ry", "rz", "cnot"),
                    queue=int(entry.get("pending_jobs", 0) or 0),
                )
        raise BackendError(f"IonQ has no backend {self._target!r}; try 'simulator'")

    def submit(self, circuit: Circuit, shots: int) -> Job:
        self.check_shots(shots)
        payload = {
            "target": self._target,
            "shots": shots,
            "input": {
                "gateset": "qis",
                "qubits": circuit.wires,
                "circuit": _circuit_body(circuit),
            },
        }
        response = requests.post(f"{BASE}/jobs", headers=self.headers, json=payload, timeout=60)
        if response.status_code not in (200, 201):
            raise BackendError(f"IonQ submit returned HTTP {response.status_code}: {response.text[:200]}")
        created = response.json()
        return Job(
            provider=self.provider,
            backend=self._target,
            id=str(created["id"]),
            shots=shots,
            depth=circuit.depth(),
        )

    def status(self, job: Job) -> str:
        response = requests.get(f"{BASE}/jobs/{job.id}", headers=self.headers, timeout=30)
        if response.status_code != 200:
            raise BackendError(f"IonQ status returned HTTP {response.status_code}")
        return str(response.json().get("status", "unknown"))

    def result(self, job: Job) -> Result:
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            response = requests.get(f"{BASE}/jobs/{job.id}", headers=self.headers, timeout=30)
            if response.status_code != 200:
                raise BackendError(f"IonQ status returned HTTP {response.status_code}")
            body = response.json()
            status = body.get("status")
            if status == "completed":
                return self._completed(job, body)
            if status in ("failed", "canceled"):
                raise BackendError(f"IonQ job {job.id} ended {status}")
            time.sleep(2)
        raise BackendError(f"IonQ job {job.id} did not finish within {self._timeout:.0f} s")

    def cancel(self, job: Job) -> None:
        response = requests.delete(f"{BASE}/jobs/{job.id}", headers=self.headers, timeout=30)
        if response.status_code not in (200, 204):
            raise BackendError(f"IonQ cancel returned HTTP {response.status_code}")

    # -- the translation this adapter owns -------------------------------
    def _completed(self, job: Job, body: Dict) -> Result:
        url = body.get("results", {}).get("probabilities", {}).get("url")
        if not url:
            raise BackendError(f"IonQ job {job.id} has no probabilities reference")
        if url.startswith("/"):
            url = "https://api.ionq.co" + url
        response = requests.get(url, headers=self.headers, timeout=30)
        if response.status_code != 200:
            raise BackendError(f"IonQ results returned HTTP {response.status_code}")
        probabilities = response.json()
        counts: Dict[str, int] = {}
        for state, probability in probabilities.items():
            index = int(state)
            width = max(1, body.get("qubits", 2))
            label = format(index, f"0{width}b")
            counts[label] = int(round(float(probability) * job.shots))
        difference = job.shots - sum(counts.values())
        if difference:
            top = max(counts, key=counts.get)
            counts[top] += difference
        return Result(job=job, counts=counts)
