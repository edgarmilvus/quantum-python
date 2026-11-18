"""Demo 02: what the task costs on five providers, and the guard that says no.

Run: python3 chapters/chapter19/files/02_estimate.py

The same six circuits and 2,048 shots, priced on every provider the book knows. One
provider is over the budget by two orders of magnitude, and the estimate refuses it
before a job is created.
"""

from pipe import estimate, spec

task = spec.Task(name="bv-1011", qubits=4, shots=2048, provider="ibm", budget_usd=5.0)
print(f"{'task':24s}{'circuits':>13s}{'shots':>14s}{'seconds':>10s}{'USD':>13s}   verdict")
for provider in ("local", "qbraid", "ibm", "braket-iqm", "ionq"):
    priced = spec.Task(**{**task.__dict__, "provider": provider})
    print(estimate.estimate(priced).report())
print()
print(f"the cheapest provider for this task: {estimate.cheapest(task)}")
print()
print("the refusal is the point: 984.84 dollars is 197 times the budget, and the")
print("pipeline learns it from a subtraction rather than from an invoice.")
