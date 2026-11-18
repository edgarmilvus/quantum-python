"""Demo 01: the task, and the four things it refuses.

Run: python3 chapters/chapter19/files/01_spec.py

A task is a name, a size, a shot count, a provider and a budget. The dataclass refuses
the four mistakes a reader makes first, and the refusal happens before anything is
submitted.
"""

from pipe import spec

task = spec.Task(name="bv-1011", qubits=4, shots=2048, provider="ibm", budget_usd=5.0)
print("the task:", task)
print(f"  circuits: {task.circuits} (one task, one zeros calibration, four single-qubit)")
print(f"  ideal:    {task.ideal()}")
print(f"  gates:    {len(spec.bv_ops(task.secret))}")
print()

for bad in (
    dict(name="", qubits=4, shots=2048, provider="ibm"),
    dict(name="x", qubits=1, shots=2048, provider="ibm"),
    dict(name="x", qubits=4, shots=0, provider="ibm"),
    dict(name="x", qubits=4, shots=2048, provider="nonsense"),
    dict(name="x", qubits=4, shots=2048, provider="ibm", budget_usd=-1.0),
    dict(name="x", qubits=4, shots=2048, provider="ibm", secret="101"),
    dict(name="x", qubits=4, shots=2048, provider="ibm", secret="10x1"),
):
    try:
        spec.Task(**bad)
    except ValueError as error:
        print(f"  refused: {error}")
print()
print("the validation is the pipeline's first gate: a bad task costs nothing to")
print("refuse and a job in a queue costs ten minutes.")
