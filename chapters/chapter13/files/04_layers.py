"""Demo 04: more layers, and how hard the optimiser looked.

Run: python3 chapters/chapter13/files/04_layers.py

Two variables move together, and the chapter keeps them apart on purpose. The
number of layers raises the best value the ansatz can represent; the number of
restarts raises the chance of finding it. p = 2 reports 0.864 from one start and
0.964 from eight, which is the same circuit found twice and believed once.
"""

from qaoa import graph as g, optimize

instance = g.square_with_diagonal()
optimum, _ = instance.max_cut()
restarts = 8

print(f"instance: {instance.n} vertices, {instance.m} edges, optimum {optimum:g}")
print(f"{'p':>3s}{'cost':>10s}{'ratio':>9s}{'evaluations':>13s}")
best = {}
for p in (1, 2, 3, 4):
    point = optimize.optimise(instance, p, restarts=restarts)
    best[p] = point
    print(f"{p:3d}{point.cost:10.4f}{point.cost / optimum:9.4f}{point.evaluations:13d}")
print()
print(f"every row uses up to {restarts} simplex starts, so the numbers compare like with like")
print()

print("the right angles at each depth:")
for p, point in best.items():
    betas = ", ".join(f"{value:.3f}" for value in point.betas)
    gammas = ", ".join(f"{value:.3f}" for value in point.gammas)
    print(f"  p={p}: beta [{betas}]  gamma [{gammas}]")
print()

print("the same p = 2 circuit, optimised with 1, 4 and 8 starts:")
for starts in (1, 4, 8):
    point = optimize.optimise(instance, 2, restarts=starts)
    print(f"  {starts} start(s): {point.cost:.4f}  ratio {point.cost / optimum:.4f}  "
          f"in {point.evaluations} evaluations")
print()
print("the circuit did not change between those three lines. The search did.")
print()

p1 = best[1].cost / optimum
p2 = best[2].cost / optimum
print(f"p=1 to p=2 buys {p2 - p1:+.4f} of ratio for one extra parameter pair;")
print(f"p=3 buys {best[3].cost / optimum - p2:+.4f} more, and p=4 buys "
      f"{best[4].cost / optimum - best[3].cost / optimum:+.4f}.")
print("the last four digits cost two thousand evaluations and buy 0.3% of the answer.")
