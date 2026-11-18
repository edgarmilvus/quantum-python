"""Demo 02: the kernel matrix, and what a layer of the feature map buys.

Run: python3 chapters/chapter15/files/02_kernel.py

The diagonal is one by construction, the off-diagonal entries measure how alike two
points look to the circuit, and the number of layers sharpens that similarity. One
layer is too blunt to separate the arms, three are enough, and a fourth is worse.
"""

import numpy as np

from qml import classifier, data, featuremap as fm, kernel

spiral = data.spiral()
train, test = spiral.stratified(3)


def gram(points, reps: int) -> np.ndarray:
    states = [fm.state_for(point, reps=reps) for point in points]
    n = len(points)
    out = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            out[i, j] = out[j, i] = fm.fidelity(states[i], states[j])
    return out


first = gram(train.points, 3)
print(kernel.report(first, train.labels))
print()

print(f"{'reps':>5s}{'depth':>7s}{'off-diagonal':>14s}{'condition':>11s}{'test accuracy':>15s}")
for reps in (1, 2, 3, 4):
    k_train = gram(train.points, reps)
    k_cross = np.array([[fm.fidelity(fm.state_for(a, reps=reps), fm.state_for(b, reps=reps))
                         for a in train.points] for b in test.points]).T
    out = classifier.run(train.points, train.labels, test.points, test.labels, k_train, k_cross, 0.1)
    depth = len(fm.ops_for(train.points[0], reps=reps))
    print(f"{reps:5d}{depth:7d}{kernel.off_diagonal_mean(k_train):14.3f}"
          f"{kernel.condition(k_train):11.1f}{out['quantum']:15.3f}")
print()
print("three layers reach 1.000 and four fall back to 0.833: a sharper kernel is not")
print("a better one, and the condition number says why, 9 against 5.")
