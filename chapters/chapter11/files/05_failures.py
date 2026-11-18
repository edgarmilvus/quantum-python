"""Demo 05: the four ways a job fails, and the same handler for all of them.

Run: python3 chapters/chapter11/files/05_failures.py

Offline device, queue timeout, retired backend, exhausted quota. Each is a different
provider problem and the same program-level problem: a job that will not produce a result.
"""

import providers as p


class Broken(p.Backend):
    provider = "demo"
    name = "broken"

    def __init__(self, behaviour: str) -> None:
        self.behaviour = behaviour

    def profile(self):
        if self.behaviour == "retired":
            raise p.BackendError("backend retired on 2026-10-19; choose another")
        return p.Profile(provider=self.provider, backend=self.name, qubits=5, basis=("h",))

    def submit(self, circuit, shots):
        if self.behaviour == "retired":
            raise p.BackendError("backend retired on 2026-10-19; choose another")
        if self.behaviour == "offline":
            raise p.BackendError("device is offline for maintenance")
        if self.behaviour == "quota":
            raise p.BackendError("quota exhausted: 0 of 10 minutes remaining this cycle")
        return p.Job(provider=self.provider, backend=self.name, id="x", shots=shots, depth=circuit.depth())

    def status(self, job):
        return "queued"

    def result(self, job):
        raise p.BackendError("job did not complete within 120 s")

    def cancel(self, job):
        return None


def run(backend: p.Backend, circuit: p.Circuit, shots: int) -> str:
    """The handler every loop in the book uses: one place, four outcomes."""
    try:
        job = backend.submit(circuit, shots)
        result = backend.result(job)
        return f"ok: {result.shots} shots"
    except p.BackendError as error:
        return f"failed: {error}"
    finally:
        pass


circuit = p.Circuit(1).add("h", 0)
for behaviour in ("offline", "retired", "quota", "timeout"):
    print(f"{behaviour:10s} {run(Broken(behaviour), circuit, 100)}")

print()
print("the caller did not branch on provider; it branched on whether a result arrived")
print("a retry policy belongs in the loop, not in the adapter, because it is about the answer")
