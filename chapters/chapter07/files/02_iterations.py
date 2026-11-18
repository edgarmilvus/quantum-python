"""Demo 02: more iterations is not better.

Run: python3 chapters/chapter07/files/02_iterations.py
"""

import grover

for n in (3, 4, 5):
    size = 1 << n
    best = grover.optimal_iterations(size)
    print(f"n={n}, N={size}, optimal {best} iterations")
    row = []
    for steps in range(0, best + 3):
        row.append(f"k={steps}: {grover.success_probability(0, n, steps):.3f}")
    print("  " + "   ".join(row))
    print()

print("n=3 in detail:")
for steps in range(0, 7):
    print(f"  k={steps}: P = {grover.success_probability(0, 3, steps):.4f}")
print()
print("at k=3 the probability has fallen to a third, at k=4 to one percent")
print("too many iterations rotate the state past the answer")
