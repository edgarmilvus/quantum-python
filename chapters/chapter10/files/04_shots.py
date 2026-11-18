"""Demo 04: the two tallies, and what shots do to the energy.

Run: python3 chapters/chapter10/files/04_shots.py
"""

import vqe
import h2

theta = -0.2235
print(f"at the optimum theta = {theta}, two tallies per energy evaluation")
print()
print(f"{'shots':>8s}{'1 sigma (mHa)':>16s}{'energy from one simulated run':>32s}")
for shots in (1000, 4096, 10000, 24000, 50000):
    sigma = vqe.shot_sigma(theta, shots)
    z = vqe.tally(theta, "Z", shots, seed=11)
    x = vqe.tally(theta, "X", shots, seed=12)
    result = vqe.energy_from_tallies(z, x)
    error = (result["energy"] - h2.exact_ground()) * 1000
    print(f"{shots:8d}{sigma * 1000:16.2f}{result['energy']:20.6f} ({error:+7.2f} mHa)")

print()
print(f"shots for one sigma at chemical accuracy: {vqe.shots_for(theta)}")
print(f"the exact energy: {h2.exact_ground():.6f}")
print()
print("the tallies are independent draws, so the error moves with the seed")
print("the sigma is the number to quote, and it is computed in closed form")
