"""Chapter 15 harness: the dataset, the map, the kernel, the classifier, the device.

Run: python3 chapters/chapter15/files/run_ex15.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qml import classifier, data, featuremap as fm, kernel

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


ROOT = Path(__file__).resolve().parents[3]

# -- the dataset --------------------------------------------------------
section("the dataset")
spiral = data.spiral()
check(spiral.n == 12, "the spiral has twelve points")
check(spiral.counts() == (6, 6), "six of each class")
check(spiral.labels[0] == 1 and spiral.labels[1] == -1, "the arms alternate")

train, test = spiral.stratified(3)
check(train.n == 6 and test.n == 6, "the split is six and six")
check(train.counts() == (3, 3) and test.counts() == (3, 3), "and stratified")
train_idx, test_idx = spiral.split_indices(3)
check(len(train_idx) == 6 and len(test_idx) == 6, "the indices match the split")
check(not set(train_idx) & set(test_idx), "and do not overlap")

for bad in (0, -1):
    try:
        spiral.stratified(bad)
    except ValueError:
        check(True, f"take={bad} is refused")
    else:
        check(False, f"take={bad} is refused")

try:
    data.Dataset(points=((0.1, 0.1),), labels=(1,))
except ValueError:
    check(True, "a one-point dataset is refused")
else:
    check(False, "a one-point dataset is refused")

# -- the feature map ----------------------------------------------------
section("the feature map")
state = fm.state_for((0.2, 0.7))
check(abs(fm.norm(state) - 1.0) < 1e-12, "the state is normalised")
check(abs(fm.fidelity(state, state) - 1.0) < 1e-12, "the self-overlap is one")

other = fm.state_for((0.8, 0.3))
check(0 < fm.fidelity(state, other) < 1, "a different point has an overlap below one")

overlap_state = fm.zero(2)
for gate, wires, theta in fm.overlap_ops((0.2, 0.7), (0.8, 0.3)):
    overlap_state = fm.apply(overlap_state, gate, wires, theta)
check(abs(float(abs(overlap_state[0]) ** 2) - fm.fidelity(state, other)) < 1e-12,
      "the overlap circuit's all-zero probability is the fidelity")

one = fm.zero(1)
one = fm.apply(one, "h", (0,))
one = fm.apply(one, "rz", (0,), -0.4)
two = fm.zero(1)
two = fm.apply(two, "h", (0,))
two = fm.apply(two, "rz", (0,), -1.4)
check(abs(fm.fidelity(one, two) - math.cos(0.5) ** 2) < 1e-12,
      "one feature and one layer give cos-squared of the difference")

check(len(fm.ops_for((0.2, 0.7), reps=1)) == 5, "one layer is five gates on two features")
check(len(fm.ops_for((0.2, 0.7), reps=3)) == 11, "three layers are eleven")

for bad in (0, -2):
    try:
        fm.ops_for((0.2, 0.7), reps=bad)
    except ValueError:
        check(True, f"reps={bad} is refused")
    else:
        check(False, f"reps={bad} is refused")

try:
    fm.ops_for((0.2, 0.7), n=3)
except ValueError:
    check(True, "two features on three wires is refused")
else:
    check(False, "two features on three wires is refused")

# -- the kernel ---------------------------------------------------------
section("the kernel")
gram = kernel.matrix(train.points, reps=3)
check(gram.shape == (6, 6), "the training matrix is six by six")
check(bool(np.allclose(gram, gram.T)), "it is symmetric")
check(abs(kernel.mean_diagonal(gram) - 1.0) < 1e-12, "the diagonal is one")
check(0.15 < kernel.off_diagonal_mean(gram) < 0.35, "the off-diagonal mean is about 0.25")
check(kernel.condition(gram) < 20, "the condition number is below twenty")

sampled = kernel.sampled(train.points, 4096, seed=3, reps=3)
check(kernel.distance_to(gram, sampled) < 0.05, "a 4,096-shot sample is within 0.05 everywhere")

counts = {"00": 300, "01": 100, "10": 80, "11": 20}
check(abs(kernel.from_counts(counts) - 0.6) < 1e-12, "the all-zero frequency is 0.6")

for bad in ({}, {"00": 0}):
    try:
        kernel.from_counts(bad)
    except ValueError:
        check(True, "an empty histogram is refused")
    else:
        check(False, "an empty histogram is refused")

# -- the classifier -----------------------------------------------------
section("the classifier")
identity = np.eye(4)
model = classifier.fit(identity, [1, -1, 1, -1], [(0, 0)] * 4, lam=0.5)
check(abs(model.alpha[0] - 1 / 1.5) < 1e-12, "the regularised solve is one over one plus lambda")
check(classifier.accuracy([1.0, -1.0, 1.0, -1.0], [1, -1, 1, -1]) == 1.0, "a perfect score is one")

check(abs(classifier.accuracy([1.0, 1.0], [1, -1]) - 0.5) < 1e-12, "and a wrong one is a half")
check(classifier.confusion([1.0, 1.0], [1, -1])["false positive"] == 1, "the confusion counts the false positive")

for bad in (0, -1):
    try:
        classifier.fit(identity, [1, -1, 1, -1], [(0, 0)] * 4, lam=bad)
    except ValueError:
        check(True, f"a penalty of {bad} is refused")
    else:
        check(False, f"a penalty of {bad} is refused")

check(abs(classifier.rbf([(0, 0)], 1.0)[0, 0] - 1.0) < 1e-12, "an RBF of a point with itself is one")

# -- the device ---------------------------------------------------------
section("the device")
record = json.loads((ROOT / "runs/chapter15/0026-kernel-12points-57x1024-ibm/result.json").read_text())
check(record["backend"] == "ibm_fez", "the run is on ibm_fez")
check(len(record["results"]) == 57, "fifty-seven circuits came back")
check(record["shots"] == 1024, "at 1,024 shots")
check(record["transpiled_depth"] == 66, "at depth 66")
check(record["reps"] == 3, "with three layers of the map")

device, shots = kernel.device_matrix(record)
diagonal = float(np.mean([device[i, i] for i in record["train"]]))
check(abs(diagonal - 0.9827) < 1e-3, "the device's self-overlap is 0.9827")
check(diagonal < 1.0, "below one, because the circuit is not perfect")

points = [tuple(point) for point in record["points"]]
exact = np.array([
    [fm.fidelity(fm.state_for(points[a], reps=3), fm.state_for(points[b], reps=3)) for b in range(len(points))]
    for a in range(len(points))
])
mask = np.zeros(device.shape, dtype=bool)
for i in record["train"]:
    for j in record["train"] + record["test"]:
        if i != j:
            mask[i, j] = True
correlation = float(np.corrcoef(exact[mask], device[mask])[0, 1])
check(correlation > 0.8, "the measured entries correlate above 0.8 with the exact ones")
check(float(np.abs(device - exact)[mask].max()) > 0.4, "and at least one pair is off by more than 0.4")

tr = [points[i] for i in record["train"]]
te = [points[i] for i in record["test"]]
trl = [record["labels"][i] for i in record["train"]]
tel = [record["labels"][i] for i in record["test"]]
exact_run = classifier.run(tr, trl, te, tel, exact[np.ix_(record["train"], record["train"])],
                           exact[np.ix_(record["train"], record["test"])], 0.1)
device_run = classifier.run(tr, trl, te, tel, device[np.ix_(record["train"], record["train"])],
                            device[np.ix_(record["train"], record["test"])], 0.1)
check(abs(exact_run["quantum"] - 1.0) < 1e-9, "the exact kernel classifies perfectly")
check(abs(device_run["quantum"] - 0.833) < 1e-3, "the device's kernel reaches 0.833")
check(abs(device_run["classical"] - 0.667) < 1e-3, "the classical baseline reaches 0.667")

heavy = classifier.run(tr, trl, te, tel, device[np.ix_(record["train"], record["train"])],
                       device[np.ix_(record["train"], record["test"])], 0.5)
check(heavy["quantum"] < device_run["quantum"], "a heavier penalty makes the device worse")

# -- the cost -----------------------------------------------------------
section("the cost")
check(6 * (6 + 1) // 2 == 21, "six training points need twenty-one pairs")
check(21 + 6 * 6 == 57, "plus thirty-six cross pairs is fifty-seven")
check(17.0 / 57.0 < 0.35, "the recorded run cost about 0.3 seconds a circuit")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
