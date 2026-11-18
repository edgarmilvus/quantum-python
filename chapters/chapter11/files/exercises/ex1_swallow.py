"""Exercise 1 (repair): an adapter that swallows the error.

A submit-and-fetch wrapper returns an empty result when the provider fails, so the caller
sees zero shots instead of a failure and every downstream statistic divides by zero or
reports a confident nothing.

Run: python3 chapters/chapter11/files/exercises/ex1_swallow.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

import providers as p


class Failing(p.Backend):
    provider = "demo"
    name = "failing"

    def profile(self):
        return p.Profile(provider="demo", backend="failing", qubits=1, basis=("h",))

    def submit(self, circuit, shots):
        raise p.BackendError("device is offline for maintenance")

    def status(self, job):
        return "failed"

    def result(self, job):
        raise p.BackendError("no result")


def swallow(backend: p.Backend, circuit: p.Circuit, shots: int) -> p.Result:
    """The defect: an empty result instead of the error."""
    try:
        job = backend.submit(circuit, shots)
        return backend.result(job)
    except p.BackendError:
        return p.Result(job=p.Job(provider=backend.provider, backend=backend.name, id="", shots=0, depth=0), counts={})


def propagate(backend: p.Backend, circuit: p.Circuit, shots: int) -> p.Result:
    """The repair: let the caller decide what a failure means."""
    job = backend.submit(circuit, shots)
    return backend.result(job)


def checks(check: Callable[[bool, str], None]) -> None:
    circuit = p.Circuit(1).add("h", 0)
    backend = Failing()

    empty = swallow(backend, circuit, 100)
    check(empty.shots == 0, "the defect returns zero shots")
    check(empty.counts == {}, "and an empty histogram")

    try:
        empty.frequency("0")
    except ValueError:
        check(True, "a frequency on the empty result raises")
    else:
        check(False, "a frequency on the empty result raises")

    try:
        propagate(backend, circuit, 100)
    except p.BackendError as error:
        check("offline" in str(error), "the repair propagates the provider's words")
    else:
        check(False, "the repair propagates the provider's words")

    replay = p.Replay("0001-ibm-fez-bell")
    check(propagate(replay, circuit, 100).shots > 0, "the repair still returns real results")

    check(empty.job.shots == 0, "the defect's job claims zero shots")
    check(empty.counts != {"0": 0, "1": 0}, "the defect does not even fill in the outcomes")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
