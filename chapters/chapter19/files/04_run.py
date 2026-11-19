"""Demo 04: the run stage, from the record to a verdict.

Run: python3 chapters/chapter19/files/04_run.py

The pipeline reads the record, checks that its secret is the one the task asked for,
corrects the readout, and returns a report object whose `ok` says whether the peak is
the answer.
"""

from pipe import run, spec

task = spec.Task(name="bv-1011", qubits=4, shots=2048, provider="ibm")
record = run.load("chapter19/0039-bv-1011-pipeline-2048-ibm")
report = run.run(record, task, seconds=4.0, usd=0.0)
print(report.report())
print()
print(f"ok: {report.ok}; the corrected peak is {report.corrected_share:.4f}")
print()

wrong = spec.Task(name="bv-other", qubits=4, shots=2048, provider="ibm", secret="0110")
try:
    run.run(record, wrong)
except ValueError as error:
    print(f"refused: {error}")
print()
print("the secret check is the pipeline's second gate: a record of one experiment")
print("cannot be reported as another, and the failure names both.")
