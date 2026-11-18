"""Demo 05: Grover against the two classical searches, at the same sizes.

Run: python3 chapters/chapter07/files/05_classical.py

Grover beats a linear scan and loses to a binary search on sorted data. The table is the
honest form of the claim, and it is why the algorithm is described as a search of an
*unsorted* list.
"""

import math

import grover

print(f"{'N':>8s}{'linear':>9s}{'Grover':>9s}{'binary':>9s}{'Grover/linear':>15s}{'Grover/binary':>15s}")
for n in (4, 6, 8, 10, 12, 20):
    size = 1 << n
    linear = grover.classical_queries(size)
    g = grover.optimal_iterations(size)
    binary = grover.binary_search_queries(size)
    print(f"{size:8d}{linear:9d}{g:9d}{binary:9d}{linear / g:15.1f}{g / binary:15.1f}")

print()
size = 1 << 20
print(f"at a million items: linear {grover.classical_queries(size)}, "
      f"Grover {grover.optimal_iterations(size)}, binary {grover.binary_search_queries(size)}")
print()
print("Grover is a square-root improvement over scanning, which is the only fair comparison")
print("against a sorted list, a binary search is logarithmically better and always will be")
print()
print("the crossover is the point: sorting costs n log n, and Grover does not sort")
for n in (10, 12, 14):
    size = 1 << n
    print(f"  N={size}: sorting ~{math.ceil(size * math.log2(size))} comparisons, "
          f"Grover {grover.optimal_iterations(size)} iterations")
