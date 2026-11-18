"""Demo 06: what the loop costs, in circuits and in seconds.

Run: python3 chapters/chapter13/files/06_budget.py

A QAOA optimisation is not one circuit. The gradient shifts one gate at a time,
so a p-layer circuit on a graph with m edges needs 2p + 2pm evaluations per step,
and each evaluation is a run at the shot count the precision demands. The numbers
here are the chapter's answer to "why is this hard on hardware".
"""

import json
from pathlib import Path

import numpy as np

from qaoa import graph as g, optimize

ROOT = Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/0022-ibm-fez-qaoa/result.json").read_text())
instance = g.square_with_diagonal()

print("the precision the optimiser needs:")
spread = 1.13  # the per-shot standard deviation of the cut, measured in demo 05
for gap in (0.5, 0.2, 0.1, 0.05, 0.01):
    shots = optimize.shots_to_resolve(gap, spread, 2.0)
    print(f"  a gap of {gap:.2f} at two sigma needs {shots:6d} shots")
print()
print(f"the hardware run used {record['shots']} shots a circuit, which resolves "
      f"{2 * spread / np.sqrt(record['shots']):.3f} of cut")
print()

print("the gradient's circuit count, per layer and per edge:")
print(f"{'p':>3s}{'edges':>7s}{'circuits per gradient':>24s}{'circuits for 20 steps':>24s}")
for p in (1, 2, 3, 4):
    counts = optimize.budget(p, instance.m, record["shots"], 20)
    print(f"{p:3d}{instance.m:7d}{counts['circuits per gradient']:24.0f}{counts['circuits for the run']:24.0f}")
print()

budget = optimize.budget(1, instance.m, record["shots"], 20)
print(f"at p=1 that is {budget['circuits for the run']:.0f} circuits and "
      f"{budget['shots for the run']:.0f} shots.")
seconds_per_circuit = 12.0 / len(record["results"])
print(f"the recorded run spent 12 seconds of runtime on 36 circuits, "
      f"{seconds_per_circuit:.2f} s a circuit,")
print(f"so 20 gradient steps would spend about {budget['circuits for the run'] * seconds_per_circuit:.0f} seconds.")
print(f"the account had 576 seconds left, which is why the chapter scans a grid instead:")
print(f"36 circuits, one job, {12.0:.0f} seconds, and the landscape is a fact rather than a search.")
print()
print("the last row is the argument against p=4 on hardware:")
deep = optimize.budget(4, instance.m, record["shots"], 20)
print(f"  p=4 needs {deep['circuits for the run']:.0f} circuits for 20 steps, "
      f"{deep['circuits for the run'] * seconds_per_circuit:.0f} seconds of runtime,")
print(f"  and it buys {0.9999 - 0.9967:.4f} of approximation ratio over p=3.")
