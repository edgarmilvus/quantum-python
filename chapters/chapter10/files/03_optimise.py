"""Demo 03: a derivative-free optimiser, and what it costs.

Run: python3 chapters/chapter10/files/03_optimise.py
"""

import vqe

print(f"{'start':>18s}{'angle':>12s}{'energy':>12s}{'evaluations':>13s}")
for lo, hi in ((-1.0, 1.0), (-3.0, 3.0), (-0.5, 0.5), (0.0, 3.0)):
    result = vqe.golden_section(vqe.energy_exact, lo=lo, hi=hi)
    print(f"{f'[{lo:.1f}, {hi:.1f}]':>18s}{result['angle']:12.6f}{result['energy']:12.6f}"
          f"{int(result['evaluations']):13d}")

print()
print("the golden section needs about forty evaluations and finds the same angle from every bracket")
print("a gradient-based optimiser would need about ten, and would need analytic gradients")
print()
print(f"the exact minimum: {vqe.golden_section(vqe.energy_exact)['energy']:.6f}")
