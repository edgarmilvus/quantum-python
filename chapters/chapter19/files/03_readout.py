"""Demo 03: the calibration turns 0.955 into 0.988.

Run: python3 chapters/chapter19/files/03_readout.py

The recorded run carries five calibration circuits. The pipeline reads the two directed
rates per qubit, builds the matrix, inverts it, and moves the peak of the BV run from
95.5% to 98.8%.
"""

from pipe import run, spec

record = run.load("0039-ibm-fez-pipeline")
model = run.readout(record)
print(model.report())
print(f"the matrix is 16 by 16, tensored from four 2 by 2 models, "
      f"determinant {float(__import__('numpy').linalg.det(model.matrix())):.4f}")
print()

before = {key: value / sum(record["counts"].values()) for key, value in record["counts"].items()}
after = run.correct(record["counts"], model)
print(f"{'outcome':8s}{'raw':>9s}{'corrected':>11s}")
for key in sorted(set(before) | set(after), key=lambda k: -after.get(k, 0))[:6]:
    print(f"{key:8s}{before.get(key, 0):9.4f}{after.get(key, 0):11.4f}")
print()
print(f"the secret is {record['secret']}: raw {run.top(before)[1]:.4f}, corrected {run.top(after)[1]:.4f}")
print()
print("the correction is chapter 12's arithmetic on chapter 18's metric: the same")
print("matrix inversion, applied to the peak of a Bernstein-Vazirani run.")
