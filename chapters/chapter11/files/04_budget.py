"""Demo 04: the guard that refuses before the money is spent.

Run: python3 chapters/chapter11/files/04_budget.py

The ledger knows three things the loop does not: the price of each provider, how much has
already been spent, and whether live mode is on. It refuses a job that would cross any of
the three.
"""

import providers as p

circuit = p.Circuit(2).add("h", 0).add("cx", 0, 1)
replay = p.Replay("0001-ibm-fez-bell")

ledger = p.Ledger(cap_usd=150.0, live=False)
print("a fresh ledger, live mode off, a hundred and fifty dollars of cap")
try:
    ledger.authorise(replay, 1024)
    print("  replay backend: authorised at 0.00 USD")
except p.BackendError as error:
    print(f"  refused: {error}")

class FakeQPU(p.Backend):
    provider = "ionq"
    name = "qpu.forte-1"

    def profile(self):
        return p.Profile(provider="ionq", backend=self.name, qubits=36, basis=("h", "cnot"))

    def submit(self, circuit, shots):
        raise NotImplementedError

    def status(self, job):
        return "submitted"

    def result(self, job):
        raise NotImplementedError

qpu = FakeQPU()
try:
    ledger.authorise(qpu, 1024)
except p.BackendError as error:
    print(f"  QPU with live off: refused: {str(error)[:70]}...")

ledger.live = True
cost = ledger.authorise(qpu, 1024)
print(f"  QPU with live on: 1024 shots costs {cost:.2f} USD")

ledger.commit(qpu, 1024)
print(f"  after committing: {ledger.spent_usd:.2f} USD of {ledger.cap_usd:.2f}")
try:
    ledger.authorise(qpu, 50_000)
except p.BackendError as error:
    print(f"  50,000 more: refused: {str(error)[:70]}...")
print()
print(ledger.report())
