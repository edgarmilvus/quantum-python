"""One place that knows which providers exist and which are usable right now."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # the demos may run from anywhere inside the clone
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[4] / ".env")
except Exception:  # pragma: no cover - dotenv is optional for the harness
    pass
from typing import Dict, List, Optional

from .base import Backend, BackendError
from .budget import PRICES, Ledger
from .replay import Replay


@dataclass(frozen=True)
class Spec:
    name: str
    provider: str
    needs: tuple
    note: str = ""


SPECS: Dict[str, Spec] = {
    "ionq": Spec("ionq", "ionq", ("IONQ_API_KEY",), "simulator is free, QPU is billed"),
    "ibm": Spec("ibm", "ibm", ("QISKIT_IBM_TOKEN",), "10 minutes of runtime per 28 days"),
    "qi": Spec("qi", "quantum_inspire", (), "needs `qi login`, not a key"),
    "braket": Spec("braket", "braket-qpu", ("AWS_ACCESS_KEY_ID",), "not implemented in this chapter"),
    "azure": Spec("azure", "azure", ("AZURE_QUANTUM_WORKSPACE",), "not implemented in this chapter"),
    "dwave": Spec("dwave", "dwave", ("DWAVE_API_TOKEN",), "Trial plan has no token since 2026"),
    "qbraid": Spec("qbraid", "qbraid", ("QBRAID_API_KEY",), "aggregator: IBM, IonQ, IQM, Rigetti behind one key"),
}


def configured() -> List[str]:
    """The providers whose credentials are present, in a stable order."""
    return [name for name, spec in SPECS.items() if all(os.getenv(var) for var in spec.needs)]


def status_table() -> str:
    width = max(len(name) for name in SPECS)
    lines = []
    for name, spec in SPECS.items():
        present = all(os.getenv(var) for var in spec.needs)
        mark = "ready" if present else "needs " + ", ".join(spec.needs)
        lines.append(f"{name:{width}s}  {mark:40s} {spec.note}")
    return "\n".join(lines)


def make(name: str, **kwargs) -> Backend:
    """Build a backend by name, with a clear error when it is not configured."""
    if name.startswith("replay:"):
        return Replay(name.split(":", 1)[1])
    if name not in SPECS:
        raise BackendError(f"unknown provider {name!r}; known: {sorted(SPECS)}")
    spec = SPECS[name]
    missing = [var for var in spec.needs if not os.getenv(var)]
    if missing:
        raise BackendError(f"{name} needs {', '.join(missing)}; use replay:<case> instead")
    if name == "ionq":
        from .ionq import IonQ

        return IonQ(**kwargs)
    if name == "ibm":
        from .ibm import IBM

        return IBM(**kwargs)
    if name == "qbraid":
        from .qbraid import Qbraid

        return Qbraid(**kwargs)
    raise BackendError(f"{name} is configured but not implemented in this chapter; see chapter 13")


def ledger(cap_usd: Optional[float] = None) -> Ledger:
    from math import inf

    cap = float(os.getenv("QUANTUM_MAX_SPEND_USD", "5")) if cap_usd is None else cap_usd
    live = os.getenv("QUANTUM_LIVE", "0") == "1"
    return Ledger(cap_usd=cap, live=live)
