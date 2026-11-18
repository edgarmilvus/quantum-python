"""Demo 05: the kernel matrix is n squared circuits, and that is the whole bill.

Run: python3 chapters/chapter15/files/05_cost.py

A kernel method needs one number per pair of points. A quantum kernel measures each
number with its own circuit, so a dataset of n points costs n(n+1)/2 training
circuits plus n x m cross circuits, before any classification happens. The
classical RBF costs nothing: it is a closed form.

The numbers here are the recorded run's: 57 circuits, 1,024 shots, 17 seconds of
runtime, seventeen seconds for a six by six problem.
"""

from qml import data

SPIRAL = data.spiral()
TRAIN, TEST = SPIRAL.stratified(3)
SHOTS = 1024
SECONDS_PER_CIRCUIT = 17.0 / 57.0
MEASURED = {"train": 6, "test": 6, "circuits": 57, "seconds": 17.0}


def circuits(n_train: int, n_test: int) -> int:
    """The distinct pairs: the training block is symmetric, the cross block is not."""
    if n_train < 1 or n_test < 0:
        raise ValueError(f"a split needs a training set, got {n_train} and {n_test}")
    return n_train * (n_train + 1) // 2 + n_train * n_test


print(f"the recorded run: {MEASURED['circuits']} circuits for {MEASURED['train']} training and "
      f"{MEASURED['test']} test points, {MEASURED['seconds']:.0f} seconds of runtime")
print(f"which is {SECONDS_PER_CIRCUIT:.3f} seconds per circuit at {SHOTS} shots")
print()

print(f"{'points':>7s}{'pairs':>9s}{'shots':>12s}{'seconds':>10s}{'hours':>8s}")
for n in (6, 12, 25, 50, 100, 250, 500, 1000):
    pairs = circuits(n, n // 2)
    seconds = pairs * SECONDS_PER_CIRCUIT
    print(f"{n:7d}{pairs:9d}{pairs * SHOTS:12d}{seconds:10.0f}{seconds / 3600:8.2f}")
print()
print("the classical RBF computes the same matrix in one line and no seconds;")
print("the quantum kernel's bill is not the classifier, it is the survey.")
print()
print(f"the chapter's six-plus-six dataset is {circuits(6, 6)} circuits, which is")
print(f"affordable. A hundred training points is {circuits(100, 50):,} circuits, which is")
print(f"an afternoon, and a thousand is {circuits(1000, 500):,}, which is eighty-three hours.")
print()
print("this is why the honest claim for quantum kernels is not speed:")
print("it is that the kernel is a different, possibly better, geometry, and that")
print("the price of measuring it is quadratic in the points before it buys anything.")
