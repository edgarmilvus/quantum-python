"""A backend that returns what a real one returned, from a file.

Every recorded run in this book is a job that ran once. This backend serves those jobs
again, which is what makes the chapters runnable on a machine with no account.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from .base import Backend, BackendError, Circuit, Job, Profile, Result

DEFAULT_ROOT = Path(__file__).resolve().parents[4] / "runs"


class Replay(Backend):
    """Reads runs/<case>/result.json and answers as the provider did."""

    def __init__(self, case: str, root: Optional[Path] = None) -> None:
        self.name = case
        self.provider = "replay"
        self._root = Path(root) if root else DEFAULT_ROOT
        path = self._root / case / "result.json"
        if not path.exists() and re.fullmatch(r"\d{4}", case):
            # A reader writes replay:0029; the folder is runs/chapter16/0029-...
            matches = sorted(self._root.glob(f"*/{case}-*/result.json"))
            if len(matches) == 1:
                path = matches[0]
        if not path.exists():
            raise BackendError(f"no recorded run at {path}")
        self._record = json.loads(path.read_text())
        counts = self._record.get("counts")
        probabilities = self._record.get("probabilities")
        if counts:
            self._counts = self._flatten(counts)
        elif probabilities:
            # IonQ's simulator returns probabilities; a replay needs counts, so scale them.
            shots = int(self._record.get("shots", 1024))
            scaled = {str(k): int(round(float(v) * shots)) for k, v in probabilities.items()}
            difference = shots - sum(scaled.values())
            if difference:
                top = max(scaled, key=scaled.get)
                scaled[top] += difference
            self._counts = {format(int(k), "02b"): v for k, v in scaled.items()}
        else:
            raise BackendError(f"{path} has neither counts nor probabilities")

    @staticmethod
    def _flatten(counts: Dict) -> Dict[str, int]:
        """Chapter 4 to 10 runs store one histogram; the multi-circuit ones nest."""
        if all(isinstance(v, int) for v in counts.values()):
            return dict(counts)
        first = next(iter(counts.values()))
        if isinstance(first, dict):
            return {k: int(v) for k, v in first.items()}
        raise BackendError(f"cannot read counts shaped like {type(first).__name__}")

    def cases(self) -> List[str]:
        return sorted(str(path.parent.relative_to(self._root))
                      for path in self._root.glob("*/*/result.json"))

    def profile(self) -> Profile:
        record = self._record
        return Profile(
            provider="replay",
            backend=str(record.get("backend", self.name)),
            qubits=int(
                record.get("backend_qubits")
                or record.get("num_qubits")
                or (1 << int(record.get("n", 1)))
                or 0
            ),
            basis=tuple(record.get("basis_gates", ())),
            queue=0,
            retires_on=str(record.get("recorded_at", "")),
        )

    def submit(self, circuit: Circuit, shots: int) -> Job:
        self.check_shots(shots)
        return Job(
            provider=self.provider,
            backend=str(self._record.get("backend", self.name)),
            id=self.name,
            shots=sum(self._counts.values()),
            depth=circuit.depth(),
            replay=True,
        )

    def status(self, job: Job) -> str:
        return "completed"

    def result(self, job: Job) -> Result:
        return Result(job=job, counts=dict(self._counts))
