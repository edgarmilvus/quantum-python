"""Chapter 11 harness: the interface, the replay, the budget, the failures.

Run: python3 chapters/chapter11/files/run_ex11.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import providers as p

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


BELL = p.Circuit(2).add("h", 0).add("cx", 0, 1)

# -- the circuit --------------------------------------------------------
section("the circuit type")
check(BELL.wires == 2, "the bell circuit has two wires")
check(len(BELL.ops) == 2, "and two operations")
check(BELL.depth() == 2, "its depth is two")
check(BELL.add("x", 1).depth() == 3, "adding an operation on a wire extends it")
check(p.Circuit(2).depth() == 0, "an empty circuit has depth zero")
check(BELL.labels() == ["00", "01", "10", "11"], "the labels are the basis strings")

for bad in (0, -1):
    try:
        p.Circuit(bad)
    except ValueError:
        check(True, f"{bad} wires is refused")
    else:
        check(False, f"{bad} wires is refused")

try:
    p.Circuit(2).add("x", 5)
except ValueError:
    check(True, "a wire outside the circuit is refused")
else:
    check(False, "a wire outside the circuit is refused")

# -- the replay ---------------------------------------------------------
section("the replay backend")
replay = p.Replay("chapter18/0001-bell-1024-ibm")
job = replay.submit(BELL, 1024)
check(job.replay is True, "the job is marked as a replay")
check(replay.status(job) == "completed", "a replay is always finished")
result = replay.result(job)
check(sum(result.counts.values()) == result.shots, "the counts add up to the shots")
check(abs(result.frequency("10") - 0.0283) < 1e-4, "the frequency of 10 is 0.0283")
check(len(result.counts) == 4, "the device histogram has four outcomes")
profile = replay.profile()
check(profile.backend == "ibm_fez", "the profile names the device")
check(profile.qubits == 156, "and its width")

probability_case = p.Replay("chapter18/0003-bell-1024-ionq")
probability_result = probability_case.result(probability_case.submit(BELL, 1024))
check(set(probability_result.counts) == {"00", "11"}, "a probability record becomes two outcomes")
check(abs(probability_result.frequency("00") - 0.5) < 1e-9, "and fifty percent on each")

try:
    p.Replay("no-such-run")
except p.BackendError:
    check(True, "an unknown case is refused")
else:
    check(False, "an unknown case is refused")

for bad in (0, -5, 200_000):
    try:
        replay.submit(BELL, bad)
    except p.BackendError:
        check(True, f"{bad} shots is refused")
    else:
        check(False, f"{bad} shots is refused")

# -- the budget ---------------------------------------------------------
section("the budget")
ledger = p.Ledger(cap_usd=100.0, live=False)
check(ledger.quote("ionq", 1024) > 80, "a thousand shots on a QPU costs more than eighty dollars")
check(ledger.quote("ionq", 100) < 10, "a hundred costs under ten")
check(ledger.quote("replay", 10_000) == 0.0, "a replay costs nothing")


class FakeQPU(p.Backend):
    provider = "ionq"
    name = "fake"

    def profile(self):
        return p.Profile(provider="ionq", backend="fake", qubits=36, basis=("h",))

    def submit(self, circuit, shots):
        raise NotImplementedError

    def status(self, job):
        return "submitted"

    def result(self, job):
        raise NotImplementedError


qpu = FakeQPU()
try:
    ledger.authorise(qpu, 100)
except p.BackendError as error:
    check("live" in str(error), "live mode off refuses a paying provider")

ledger.live = True
cost = ledger.authorise(qpu, 100)
check(abs(cost - 8.3) < 0.01, "a hundred shots costs 8.30")
ledger.commit(qpu, 100)
check(abs(ledger.spent_usd - 8.3) < 0.01, "the ledger records it")

try:
    ledger.authorise(qpu, 1024)
except p.BackendError as error:
    check("cap" in str(error), "a second job over the cap is refused")

check(ledger.report().count("USD") >= 2, "the report quotes each entry and the total")

try:
    ledger.quote("nonsense", 100)
except p.BackendError:
    check(True, "an unknown provider has no price")
else:
    check(False, "an unknown provider has no price")

try:
    p.PRICES["ionq"].quote(0)
except ValueError:
    check(True, "a zero-shot quote is refused")
else:
    check(False, "a zero-shot quote is refused")

# -- the registry -------------------------------------------------------
section("the registry")
check(set(p.SPECS) == {"ionq", "ibm", "qi", "braket", "azure", "dwave", "qbraid"},
      "seven providers are known, the aggregator among them")
check("replay" not in p.SPECS, "the replay is not a provider")
table = p.status_table()
check("ionq" in table and "needs" in table, "the status table names each provider and its need")

saved = {name: os.environ.get(name) for name in ("IONQ_API_KEY", "QISKIT_IBM_TOKEN")}
try:
    for name in saved:
        os.environ.pop(name, None)
    try:
        p.make("ionq")
    except p.BackendError as error:
        check("IONQ_API_KEY" in str(error), "a missing key is refused by name")
    try:
        p.make("ibm")
    except p.BackendError as error:
        check("QISKIT_IBM_TOKEN" in str(error), "the IBM key is refused by name")
    try:
        p.make("nonsense")
    except p.BackendError as error:
        check("unknown provider" in str(error), "an unknown provider is refused")
    check(p.configured() == [] or "ionq" not in p.configured(), "nothing is configured without keys")
finally:
    for name, value in saved.items():
        if value is not None:
            os.environ[name] = value

check(p.make("replay:0001").provider == "replay", "the replay is built by name")
# The aggregator only needs a key string to be constructed; the check below never
# submits. A clone with no .env must still reach this line, so the harness lends
# it one and gives the environment back afterwards.
saved_qbraid = os.environ.get("QBRAID_API_KEY")
os.environ["QBRAID_API_KEY"] = saved_qbraid or "offline-test"
try:
    check(p.make("qbraid").name.startswith("qbraid:"), "the aggregator is built by name, with its device")
finally:
    if saved_qbraid is None:
        os.environ.pop("QBRAID_API_KEY", None)
    else:
        os.environ["QBRAID_API_KEY"] = saved_qbraid

# -- the failures -------------------------------------------------------
section("the four failures")


class Broken(p.Backend):
    provider = "demo"
    name = "broken"

    def __init__(self, behaviour: str) -> None:
        self.behaviour = behaviour

    def profile(self):
        return p.Profile(provider="demo", backend="broken", qubits=1, basis=("h",))

    def submit(self, circuit, shots):
        if self.behaviour == "offline":
            raise p.BackendError("device is offline for maintenance")
        if self.behaviour == "retired":
            raise p.BackendError("backend retired on 2026-10-19; choose another")
        if self.behaviour == "quota":
            raise p.BackendError("quota exhausted: 0 of 10 minutes remaining")
        return p.Job(provider="demo", backend="broken", id="x", shots=shots, depth=circuit.depth())

    def status(self, job):
        return "queued"

    def result(self, job):
        raise p.BackendError("job did not complete within 120 s")


small = p.Circuit(1).add("h", 0)
for behaviour, word in (
    ("offline", "offline"),
    ("retired", "retired"),
    ("quota", "quota"),
    ("timeout", "complete"),
):
    try:
        backend = Broken(behaviour)
        job = backend.submit(small, 10)
        backend.result(job)
    except p.BackendError as error:
        check(word in str(error), f"{behaviour} says {word}")
    else:
        check(False, f"{behaviour} raises")

try:
    Broken("offline").cancel(p.Job(provider="demo", backend="b", id="x", shots=1, depth=1))
except p.BackendError:
    check(True, "a backend without cancel refuses it")
else:
    check(False, "a backend without cancel refuses it")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
