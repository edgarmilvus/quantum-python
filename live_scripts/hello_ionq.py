"""Minimal IonQ check: submit a Bell pair to the simulator over the REST API.

No SDK required, which keeps the chapter's dependency surface at zero for the
provider it is not about. Reads IONQ_API_KEY from .env.
"""

import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv(".env", override=True)
token = os.getenv("IONQ_API_KEY", "")
if not token:
    raise SystemExit("missing IONQ_API_KEY in .env")

BASE = "https://api.ionq.co/v0.3"
HEADERS = {"Authorization": f"apiKey {token}", "Content-Type": "application/json"}

job = {
    "target": "simulator",
    "shots": 1024,
    "input": {
        "gateset": "qis",
        "qubits": 2,
        "circuit": [
            {"gate": "h", "target": 0},
            {"gate": "cnot", "control": 0, "target": 1},
        ],
    },
}
r = requests.post(f"{BASE}/jobs", headers=HEADERS, json=job, timeout=60)
r.raise_for_status()
created = r.json()
job_id = created["id"]
print(f"job id: {job_id}", flush=True)

while True:
    s = requests.get(f"{BASE}/jobs/{job_id}", headers=HEADERS, timeout=60).json()
    status = s.get("status")
    print(f"  status: {status}", flush=True)
    if status in ("completed", "canceled", "failed"):
        break
    time.sleep(2)

if status != "completed":
    raise SystemExit(f"job ended {status}: {json.dumps(s)[:400]}")

# Since 2026 the job carries probabilities by reference, not a histogram.
url = s.get("results", {}).get("probabilities", {}).get("url")
if not url:
    raise SystemExit(f"no probabilities in job: {json.dumps(s)[:400]}")
if url.startswith("/v0.4/"):
    url = "https://api.ionq.co" + url
probs = requests.get(url, headers=HEADERS, timeout=60).json()
print(f"probabilities: {dict(sorted(probs.items()))}", flush=True)
for state, p in sorted(probs.items()):
    print(f"  P({state}) = {p:.4f}", flush=True)
