"""Demo 03: the one-layer landscape, drawn as characters.

Run: python3 chapters/chapter13/files/03_landscape.py

The cost is a smooth function of two angles, and its maximum is a plateau rather
than a spike: a grid of 12 by 12 finds 3.2316 where the optimiser finds 3.2371.
The printed map is the same object a heatmap would show, in text, so a reader can
see why a coarse grid is enough to start a simplex and not enough to finish one.
"""

import numpy as np

from qaoa import graph as g, optimize

instance = g.square_with_diagonal()
optimum, _ = instance.max_cut()
steps = 12
grid = optimize.landscape(instance, steps, steps)
betas = np.linspace(0.0, np.pi / 2, steps)
gammas = np.linspace(0.0, np.pi, steps)

ramp = " .:-=+*#%@"
low, high = grid.min(), grid.max()
print(f"expected cut over beta in [0, pi/2] and gamma in [0, pi], {steps} x {steps} points")
print(f"low {low:.4f}, high {high:.4f}, optimum {optimum:g}")
print()
print("      gamma ->")
print("beta  " + "".join(f"{gamma:5.2f}" for gamma in gammas[::3]))
for i, beta in enumerate(betas):
    row = "".join(ramp[min(len(ramp) - 1, int((value - low) / (high - low) * (len(ramp) - 1)))] for value in grid[i])
    print(f"{beta:5.2f} {row}")
print()
print("@ is the highest point of the grid, a blank is the lowest")

best = np.unravel_index(int(np.argmax(grid)), grid.shape)
print()
print(f"grid maximum {grid[best]:.4f} at beta {betas[best[0]]:.4f}, gamma {gammas[best[1]]:.4f}")
print(f"the optimiser reaches {optimize.optimise(instance, 1).cost:.4f}, so the grid costs "
      f"{optimize.optimise(instance, 1).cost - grid[best]:.4f} of the value")
print()
within = float(np.mean(grid > grid.max() - 0.05))
print(f"{within:.1%} of the grid sits within 0.05 of its maximum: the peak is narrow,")
print("so where the grid points fall matters as much as how many there are.")

coarse = optimize.grid_search(instance, 1, 6, 6)
print()
print(f"the 6 by 6 grid the hardware run used finds {coarse.cost:.4f} at "
      f"beta {coarse.betas[0]:.4f}, gamma {coarse.gammas[0]:.4f}")
print(f"that is {coarse.cost / optimum:.4f} of the optimum, and it is the best a device")
print("with 36 circuits can see.")
shifted = optimize.grid_search(instance, 1, 6, 6,
                               (np.pi / 20, np.pi / 2 + np.pi / 20),
                               (np.pi / 10, np.pi + np.pi / 10))
print()
print(f"move the same 36 points by half a step and the best is {shifted.cost:.4f},")
print(f"or {shifted.cost / optimum:.4f} of the optimum: the same budget, 5 points worse,")
print("because the peak fell between the grid points.")
