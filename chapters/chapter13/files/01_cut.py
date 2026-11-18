"""Demo 01: the instance, and what guessing already achieves.

Run: python3 chapters/chapter13/files/01_cut.py

MaxCut on a square with one diagonal. Four vertices is small enough that all 16
splits can be listed, so the optimum is a fact and not an estimate: the number
QAOA has to beat is 4, and the number a coin flip achieves is 2.5.
"""

from qaoa import graph as g

instance = g.square_with_diagonal()
print(instance.report())
print()

optimum, best = instance.max_cut()
winners = [format(bits, "04b") for bits, value in instance.all_cuts().items() if value == optimum]
print(f"optimum {optimum:g}, reached by {' and '.join(winners)}, and nothing else")
print(f"a uniform guess averages {instance.uniform_mean():g}")
print()

print(f"{'bits':8s}{'cut':>5s}   assignment")
for bits, value in instance.all_cuts().items():
    mark = "  <- optimal" if value == optimum else ""
    print(f"{format(bits, '04b'):8s}{value:5g}   {instance.assignment(bits)}{mark}")
print()

print("how many assignments reach each cut value:")
for value, count in instance.spectrum().items():
    print(f"  cut {value:g}: {count:2d} of 16 assignments")
print()
print("the gap between 4 and 2.5 is what the circuit has to close, and the 12.5%")
print("chance of sampling an optimal assignment is what it has to raise.")
