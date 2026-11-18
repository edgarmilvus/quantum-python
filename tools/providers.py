#!/usr/bin/env python3
"""Show which providers answer, without spending anything.

Usage:
  python3 tools/providers.py --check    # who is reachable
  python3 tools/providers.py --budget   # remaining free allowance, where reported

No secrets are printed: only lengths, backend names and status codes.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)


def check_ibm() -> str:
    from qiskit_ibm_runtime import QiskitRuntimeService

    import os

    if not os.getenv("QISKIT_IBM_TOKEN") or not os.getenv("QISKIT_IBM_INSTANCE"):
        return "skipped (no token or instance)"
    service = QiskitRuntimeService(channel="ibm_quantum_platform")
    backends = service.backends()
    names = ", ".join(f"{b.name}({b.num_qubits}q)" for b in backends)
    return f"ok, {len(backends)} backends: {names}"


def check_qi() -> str:
    from qiskit_quantuminspire.qi_provider import QIProvider

    provider = QIProvider()
    rows = [f"{b.name}={b.status.name}" for b in provider.backends()]
    return f"ok, {len(rows)} backends: " + ", ".join(rows)


def check_ionq() -> str:
    import os

    import requests

    token = os.getenv("IONQ_API_KEY")
    if not token:
        return "skipped (no key)"
    r = requests.get(
        "https://api.ionq.co/v0.3/backends",
        headers={"Authorization": f"apiKey {token}"},
        timeout=30,
    )
    if r.status_code != 200:
        return f"HTTP {r.status_code}"
    backends = r.json()
    available = [b["backend"] for b in backends if b.get("status") == "available"]
    return f"ok, {len(backends)} backends, available: {', '.join(available)}"


def check_dwave() -> str:
    import os

    if os.getenv("DWAVE_API_TOKEN"):
        return "token present"
    return "no token (Trial plan has none)"


def check_braket() -> str:
    import os

    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AMZN_BRAKET_OUT_S3_BUCKET"):
        return "keys present (not exercised)"
    return "not configured"


def check_azure() -> str:
    import os

    if os.getenv("AZURE_QUANTUM_WORKSPACE"):
        return "workspace configured (not exercised)"
    return "not configured"


CHECKS = {
    "IBM Quantum": check_ibm,
    "Quantum Inspire": check_qi,
    "IonQ": check_ionq,
    "D-Wave Leap": check_dwave,
    "Amazon Braket": check_braket,
    "Azure Quantum": check_azure,
}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("--check", "--budget"):
        raise SystemExit("usage: providers.py --check | --budget")
    width = max(len(name) for name in CHECKS)
    for name, fn in CHECKS.items():
        try:
            status = fn()
        except Exception as exc:  # a provider that fails must not hide the others
            status = f"error: {type(exc).__name__}: {exc}"
        print(f"{name:{width}s}  {status}")


if __name__ == "__main__":
    main()
