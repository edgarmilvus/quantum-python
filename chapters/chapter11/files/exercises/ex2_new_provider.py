"""Exercise 2 (extend): a new provider, added without touching the loop.

Adding a provider means one spec, one price, and one adapter class. The demo's loop does not
change, which is the test of whether the interface was worth building.

Run: python3 chapters/chapter11/files/exercises/ex2_new_provider.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import providers as p
from providers.budget import PRICES
from providers.registry import Spec


def register(specs: Dict[str, Spec], name: str, provider: str, needs: tuple) -> None:
    """Add one provider to the registry's table."""
    if name in specs:
        raise ValueError(f"{name} is already registered")
    specs[name] = Spec(name=name, provider=provider, needs=needs)


def loop(backends, circuit, shots) -> Dict[str, int]:
    """The loop that must not change when a provider is added."""
    out = {}
    for backend in backends:
        try:
            job = backend.submit(circuit, shots)
            out[backend.provider] = backend.result(job).shots
        except p.BackendError as error:
            out[backend.provider] = -1
    return out


def checks(check: Callable[[bool, str], None]) -> None:
    circuit = p.Circuit(2).add("h", 0).add("cx", 0, 1)
    replay = p.Replay("0001-ibm-fez-bell")
    check(loop([replay], circuit, 64) == {"replay": 1024}, "the loop works on a replay")

    specs = dict(p.SPECS)
    register(specs, "demo-qpu", "demo-qpu", ("DEMO_KEY",))
    check("demo-qpu" in specs, "the new provider is registered")
    check(specs["demo-qpu"].provider == "demo-qpu", "and keeps its provider name")

    try:
        register(specs, "demo-qpu", "x", ())
    except ValueError:
        check(True, "registering twice is refused")
    else:
        check(False, "registering twice is refused")

    PRICES.setdefault("demo-qpu", p.Price("demo-qpu", 1.0, 0.001, "exercise"))
    check(abs(PRICES["demo-qpu"].quote(1000) - 2.0) < 1e-9, "its price is one dollar plus a thousandth")

    ledger = p.Ledger(cap_usd=10.0, live=True)
    check(ledger.quote("demo-qpu", 1000) == 2.0, "the ledger can quote it")

    missing = [v for v in specs["demo-qpu"].needs if not __import__("os").getenv(v)]
    check(missing == ["DEMO_KEY"], "the spec says which variable is missing")

    check(loop([replay], circuit, 64) == {"replay": 1024}, "the old provider still works unchanged")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
