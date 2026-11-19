"""Demo 04: the same matrix from ibm_fez, and the error the penalty cannot fix.

Run: python3 chapters/chapter15/files/04_device.py

Reads runs/chapter15/0026-kernel-12points-57x1024-ibm/result.json: 57 circuits, depth 66, 1024 shots.
The self-overlap comes back at 0.983, the off-diagonal entries correlate 0.58 with
the exact ones, and one pair collapses from 0.49 to 0.000. That last error is not
noise, so a larger ridge penalty makes the classifier worse instead of better.
"""

import json
import pathlib

import numpy as np

from qml import classifier, featuremap as fm, kernel

ROOT = pathlib.Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/chapter15/0026-kernel-12points-57x1024-ibm/result.json").read_text())
points = [tuple(point) for point in record["points"]]
labels = record["labels"]
train, test = record["train"], record["test"]
reps = record["reps"]

device, shots = kernel.device_matrix(record)
exact = np.array([
    [fm.fidelity(fm.state_for(points[a], reps=reps), fm.state_for(points[b], reps=reps))
     for b in range(len(points))]
    for a in range(len(points))
])

print(f"job {record['job_id']} on {record['backend']}, {len(record['results'])} circuits, "
      f"{record['shots']} shots, depth {record['transpiled_depth']}")
print(f"self-overlap on the device: {np.mean([device[i, i] for i in train]):.4f} where the exact is 1.0000")
print()

mask = np.zeros(device.shape, dtype=bool)
for i in train:
    for j in train + test:
        if i != j:
            mask[i, j] = True
print(f"off-diagonal: exact mean {exact[mask].mean():.4f}, device mean {device[mask].mean():.4f}")
print(f"correlation between them: {np.corrcoef(exact[mask], device[mask])[0, 1]:.4f}")
print(f"largest single error: {np.abs(device - exact)[mask].max():.4f}")
print()

worst = np.unravel_index(int(np.argmax(np.where(mask, np.abs(device - exact), 0))), device.shape)
print(f"the pair that breaks: points {worst[0]} and {worst[1]}, exact {exact[worst]:.4f}, device {device[worst]:.4f}")
print("the overlap circuit is a destructive interference pattern; a phase error moves")
print("it from half the shots to none, and no regulariser recovers the missing half.")
print()

train_points = [points[i] for i in train]
test_points = [points[i] for i in test]
train_labels = [labels[i] for i in train]
test_labels = [labels[i] for i in test]
print(f"{'kernel':10s}{'lam':>6s}{'accuracy':>10s}")
for lam in (0.01, 0.1, 0.5):
    exact_run = classifier.run(train_points, train_labels, test_points, test_labels,
                               exact[np.ix_(train, train)], exact[np.ix_(train, test)], lam)
    device_run = classifier.run(train_points, train_labels, test_points, test_labels,
                                device[np.ix_(train, train)], device[np.ix_(train, test)], lam)
    print(f"{'exact':10s}{lam:6.2f}{exact_run['quantum']:10.3f}")
    print(f"{'device':10s}{lam:6.2f}{device_run['quantum']:10.3f}")
print()
print(f"the classical RBF on the same split reaches {device_run['classical']:.3f}")
print("the device's kernel still beats the classical one at a small penalty, 0.833")
print("against 0.667, and the exact kernel is perfect at every penalty. The gap the")
print("machine opened is the difference between a 1.000 and a 0.833, and it is made")
print("of one collapsed pair and a diagonal of 0.983 instead of 1.000.")
