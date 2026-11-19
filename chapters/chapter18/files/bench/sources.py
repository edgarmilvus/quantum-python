"""Where the benchmark rows come from: recorded runs, a local sampler, a price list.

Every row is a file or a computation, and the chapter never types a distance. The
records are the ones the book made: 0036 for the GHZ run on IBM, 0037 for the same
circuit through qBraid, and 0001, 0002 and 0003 for the Bell pair on three other
backends.

The price list is chapter 11's, kept here so a reader can see what a paid QPU would
have cost without spending it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np

from .task import Row, ideal_distribution, total_variation

ROOT = Path(__file__).resolve().parents[4]
RUNS = ROOT / "runs"

PRICES = {
    "ionq": (0.30, 0.08),
    "braket-iqm": (0.30, 0.0016),
    "ibm": (0.0, 0.0),
    "qbraid": (0.0, 0.0),
    "local": (0.0, 0.0),
}


def load(case: str) -> dict:
    return json.loads((RUNS / case / "result.json").read_text())


def quoted(provider: str, shots: int) -> float:
    """What one job would cost on a paid provider, from chapter 11's table."""
    if provider not in PRICES:
        raise KeyError(f"no price for {provider!r}; known: {sorted(PRICES)}")
    per_task, per_shot = PRICES[provider]
    if shots < 1:
        raise ValueError(f"shots must be positive, got {shots}")
    return per_task + per_shot * shots


def ibm_ghz() -> List[Row]:
    """The two GHZ circuits the IBM job returned, with the wall time of the job."""
    record = load("chapter18/0036-ghz-4096-ibm")
    ideal = ideal_distribution(3)
    rows = []
    for entry in record["results"]:
        delay = float(entry["delay_us"])
        rows.append(
            Row(
                source=f"ibm_kingston, {delay:.0f} us",
                provider="ibm",
                kind="qpu",
                tvd=total_variation(entry["counts"], ideal),
                shots=sum(entry["counts"].values()),
                wall_seconds=float(record["wall_seconds"]) if delay == 0 else 0.0,
                cost_usd=0.0,
                notes="open plan: runtime, not dollars" if delay == 0 else "same job, delayed",
            )
        )
    return rows


def qbraid_ghz() -> Row:
    """The same circuit through qBraid's gateway to IonQ's simulator."""
    record = load("chapter18/0037-ghz-4096-qbraid")
    counts = record["results"][0]["counts"]
    return Row(
        source="qbraid, IonQ simulator",
        provider="qbraid",
        kind="sim",
        tvd=total_variation(counts, ideal_distribution(3)),
        shots=sum(counts.values()),
        wall_seconds=float(record["wall_seconds"]),
        cost_usd=0.0,
        notes="exact probabilities, no sampling",
    )


def local_ghz(shots: int = 4096, seed: int = 0) -> Row:
    """An ideal sampler at the same shot count, which is the benchmark's floor."""
    ideal = ideal_distribution(3)
    keys = sorted(ideal)
    rng = np.random.default_rng(seed)
    draws = rng.multinomial(shots, [ideal[key] for key in keys])
    counts = {key: int(count) for key, count in zip(keys, draws) if count}
    return Row(
        source="local ideal, sampled",
        provider="local",
        kind="sim",
        tvd=total_variation(counts, ideal),
        shots=shots,
        wall_seconds=0.01,
        cost_usd=0.0,
        notes="shot noise only",
    )


def bell_rows() -> List[Row]:
    """The four Bell-pair sources the book recorded in its first chapters."""
    ideal = {"00": 0.5, "11": 0.5}
    rows = []
    for case, source, kind, wall, note in (
        ("chapter18/0001-bell-1024-ibm", "ibm_fez", "qpu", 0.0, "the book's first hardware run"),
        ("chapter18/0002-bell-1024-qi", "quantum inspire emulator", "sim", 0.0, "an exact emulator"),
        ("chapter18/0003-bell-1024-ionq", "IonQ simulator", "sim", 0.0, "probabilities, not counts"),
    ):
        record = load(case)
        if "counts" in record:
            counts = record["counts"]
            if isinstance(next(iter(counts.values())), dict):
                counts = next(iter(counts.values()))
        else:
            # IonQ reports probabilities keyed by the integer state, so a two-qubit
            # Bell pair arrives as {"0": 0.5, "3": 0.5} and has to be turned into
            # counts before it can be compared with one.
            shots = int(record.get("shots", 1024))
            counts = {
                format(int(state), "02b"): int(round(float(p) * shots))
                for state, p in record["probabilities"].items()
            }
        rows.append(
            Row(
                source=source,
                provider="ibm" if "ibm" in case else ("ionq" if "ionq" in case else "qi"),
                kind=kind,
                tvd=total_variation(counts, ideal),
                shots=sum(counts.values()),
                wall_seconds=wall,
                cost_usd=0.0,
                notes=note,
            )
        )
    return rows


def hypothetical(budget_rows: List[Row], provider: str = "ionq") -> Dict[str, float]:
    """What the GHZ shots would cost on a paid QPU, for each row that used one."""
    shots = max(row.shots for row in budget_rows)
    return {"provider": provider, "shots": shots, "usd": quoted(provider, shots)}


def by_provider(rows: List[Row]) -> Dict[str, float]:
    """The best distance each provider achieved, which is the ranking a reader wants."""
    out: Dict[str, float] = {}
    for row in rows:
        out[row.provider] = min(out.get(row.provider, 1.0), row.tvd)
    return dict(sorted(out.items(), key=lambda item: item[1]))
