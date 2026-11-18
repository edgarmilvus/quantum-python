"""Demo 01: a dataset a line cannot separate.

Run: python3 chapters/chapter15/files/01_dataset.py

Twelve points, two interleaved arms. The classical baseline is a kernel ridge with
an RBF kernel, tuned over six bandwidths, and it reaches 0.667 on the held-out
half: good enough to be interesting and not good enough to be right.
"""

from qml import classifier, data

spiral = data.spiral()
print(data.report(spiral))
print()

train, test = spiral.stratified(3)
print(f"train {train.n} points: {train.counts()[0]} positive, {train.counts()[1]} negative")
print(f"test  {test.n} points: {test.counts()[0]} positive, {test.counts()[1]} negative")
print()

print("the best RBF on this split, over six bandwidths:")
best = {"gamma": 0.0, "accuracy": -1.0}
for gamma in (0.5, 1.0, 2.0, 4.0, 8.0, 16.0):
    gram = classifier.rbf(train.points, gamma)
    model = classifier.fit(gram, train.labels, train.points, 0.5)
    score = model.decision(classifier.cross(train.points, test.points, gamma))
    value = classifier.accuracy(score, test.labels)
    print(f"  gamma {gamma:5.1f}: train accuracy {classifier.accuracy(model.decision(gram), train.labels):.3f}, "
          f"test accuracy {value:.3f}")
    if value > best["accuracy"]:
        best = {"gamma": gamma, "accuracy": value}
print()
print(f"best classical: {best['accuracy']:.3f} at gamma {best['gamma']}")
print("a line does worse than this, because no line separates the arms.")
