"""Demo 05: one function from a task to a report.

Run: python3 chapters/chapter19/files/05_pipeline.py

The pipeline is the four stages in order: validate, estimate, run, report. Each stage
can refuse, and the refusals are the reason the pipeline exists: a reader who runs the
stages by hand forgets one of them.
"""

from pipe import estimate, run, spec


def pipeline(task: spec.Task, case: str, seconds: float = 4.0) -> str:
    """The whole thing, in five lines: the estimate, the record, the report."""
    plan = estimate.estimate(task)
    if not plan.allowed:
        return f"{task.name}: refused before submission ({plan.reason})"
    record = run.load(case)
    report = run.run(record, task, seconds=seconds, usd=plan.usd)
    return report.report()


task = spec.Task(name="bv-1011", qubits=4, shots=2048, provider="ibm")
print(pipeline(task, "chapter19/0039-bv-1011-pipeline-2048-ibm"))
print()
print(pipeline(spec.Task(**{**task.__dict__, "provider": "ionq"}), "chapter19/0039-bv-1011-pipeline-2048-ibm"))
print()
print("the second call never reads a record: the estimate refused it first.")
print()
print("what the pipeline leaves on disk: runs/chapter19/0039-bv-1011-pipeline-2048-ibm/result.json,")
print("which holds the task's counts, the five calibration circuits, the backend and")
print("the job id. A stranger can replay it without an account, which is the last")
print("thing the pipeline promises.")
