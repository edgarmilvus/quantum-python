"""Demo 02: sweeps, success, and the sweep at which the run froze.

Run: python3 chapters/chapter14/files/02_anneal.py

The instance is twelve variables with every pair coupled. The exact optimum is
-24 and four assignments reach it. Twenty sweeps find it 76.5% of the time; a
thousand find it every time. The trace shows why: the state reaches -24 early and
then wanders out of it while the temperature is still high enough to leave.
"""

from anneal import instances, sampler

coupling = instances.spin_glass()
exact = sampler.Exact({}, coupling).sample()
optimum = exact.best()[0]
print(f"instance: 12 variables, {len(coupling)} couplings, optimum {optimum:.0f}")
print(f"ground states: {int(exact.info['ground states'])} of 4,096 assignments")
print()

print(f"{'sweeps':>8s}{'success':>10s}{'best':>8s}{'acceptance':>12s}{'distinct':>10s}")
for sweeps in (10, 25, 50, 100, 300, 1000):
    result = sampler.Annealer({}, coupling, 0.0, sweeps=sweeps, seed=11).sample(200)
    print(f"{sweeps:8d}{sampler.success_rate(result, optimum):10.3f}{result.best()[0]:8.0f}"
          f"{result.info['acceptance']:12.3f}{result.unique():10d}")
print()

print("one run at 200 sweeps, every twentieth sweep:")
for sweep, value in sampler.Annealer({}, coupling, 0.0, sweeps=200, seed=11).trace(20):
    bar = "#" * int(round((-value) * 1.5))
    print(f"  sweep {sweep:3d}  energy {value:6.1f}  {bar}")
print()
print("the state reaches the optimum by sweep 20 and leaves it again at 60,")
print("which is the temperature still being high enough to cross a barrier.")
print()

print("reads needed for a 95% chance of at least one optimal read:")
for probability in (0.99, 0.765, 0.5, 0.25, 0.1, 0.05):
    count = sampler.reads_for(probability)
    print(f"  p = {probability:.3f} -> {count:4d} read{'' if count == 1 else 's'}")
print()
print("the same number from the other side: ten reads at p = 0.25 gives")
print(f"  {1 - (1 - 0.25) ** 10:.3f}, which is why the curve is worth reading twice.")
