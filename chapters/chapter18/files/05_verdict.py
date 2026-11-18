"""Demo 05: the decision table, and what the benchmark does not measure.

Run: python3 chapters/chapter18/files/05_verdict.py

A benchmark that ranks four numbers and stops is a leaderboard. The chapter's
verdict is a table of situations and what to run in each, plus a list of the things
this benchmark cannot tell a reader.
"""

from bench import sources, task

rows = sources.ibm_ghz() + [sources.qbraid_ghz(), sources.local_ghz()]
best = min(rows, key=lambda row: row.tvd)
print(f"the best distance is {best.tvd:.4f} from {best.source}")
print()

print("situations, and what to run:")
table = [
    ("designing a circuit", "local sampler", "free, exact, instant"),
    ("checking a provider's API", "its free simulator", "free, and the shape is real"),
    ("measuring a device", "the QPU", "runtime or dollars, and a queue"),
    ("a number for a paper", "both, with the shots stated", "the comparison is the claim"),
    ("a claim about quantum advantage", "neither", "the benchmark is too small"),
]
for situation, choice, why in table:
    print(f"  {situation:32s}{choice:28s}{why}")
print()
print("what this benchmark does not measure:")
for limit in (
    "a circuit larger than three qubits, where routing dominates",
    "a gate set that differs from the one the book uses",
    "a provider's queue at a busy hour",
    "the drift of a device between two afternoons",
    "whether the task is useful for anything",
):
    print(f"  - {limit}")
print()
print("the honest sentence the chapter can defend: on a three-qubit GHZ state at")
print("4,096 shots, a good device is 0.068 away from ideal, an exact emulator is")
print("0.021 away, and a sampler on a laptop is 0.010 away because that is the shot")
print("noise. The device is the only row whose number is about a machine.")
