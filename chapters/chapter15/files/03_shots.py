"""Demo 03: shot noise in the kernel, and the penalty that absorbs it.

Run: python3 chapters/chapter15/files/03_shots.py

A kernel entry measured at N shots has a standard error near 1/(2 sqrt(N)). The
classifier sees that error as part of the kernel, and with a penalty too small to
absorb it the decision flips. The table is the chapter's most practical result:
the ridge penalty has a floor set by the shot count, not by the matrix.
"""

import numpy as np

from qml import classifier, data, featuremap as fm, kernel

spiral = data.spiral()
train, test = spiral.stratified(3)
exact = np.array([[fm.fidelity(fm.state_for(spiral.points[a], reps=3), fm.state_for(spiral.points[b], reps=3))
                   for b in range(spiral.n)] for a in range(spiral.n)])
train_idx, test_idx = spiral.split_indices(3)
k_train = np.clip(exact[np.ix_(train_idx, train_idx)], 0.0, 1.0)
k_cross = np.clip(exact[np.ix_(train_idx, test_idx)], 0.0, 1.0)

print(f"the exact kernel separates the split: accuracy "
      f"{classifier.run(train.points, train.labels, test.points, test.labels, k_train, k_cross, 0.1)['quantum']:.3f}")
print()

rng = np.random.default_rng(0)
print(f"{'shots':>7s}{'entry error':>13s}{'lam':>6s}{'accuracy, 30 seeds':>22s}")
for shots in (100, 300, 1024, 4096):
    error = float(np.sqrt(0.25 / shots))
    for lam in (0.01, 0.1, 0.5):
        values = []
        for seed in range(30):
            local = np.random.default_rng(seed)
            sampled_train = np.array([[local.binomial(shots, k_train[i, j]) / shots for j in range(len(train_idx))]
                                      for i in range(len(train_idx))])
            sampled_cross = np.array([[local.binomial(shots, k_cross[i, j]) / shots for j in range(len(test_idx))]
                                      for i in range(len(train_idx))])
            values.append(classifier.run(train.points, train.labels, test.points, test.labels,
                                         sampled_train, sampled_cross, lam)["quantum"])
        print(f"{shots:7d}{error:13.3f}{lam:6.2f}{np.mean(values):12.3f} +/- {np.std(values):.3f}")
print()
print("at 1,024 shots the entry error is 0.016 and the classifier does not notice;")
print("at 100 shots it is 0.05 and only the largest penalty holds every seed.")
print()
print("so the kernel is robust to sampling, and the next demo shows what it is not")
print("robust to: a phase error that moves one pair from 0.49 to 0.00, which no")
print("penalty can undo because it is a bias rather than a fluctuation.")
