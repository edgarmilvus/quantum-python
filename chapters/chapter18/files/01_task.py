"""Demo 01: the task, the ideal distribution, and one number.

Run: python3 chapters/chapter18/files/01_task.py

A GHZ state is H, CX, CX: the ideal is 000 and 111 at one half each, and the total
variation distance is half the L1 distance from that ideal. Two examples, one good
and one bad, calibrate the scale before any backend is involved.
"""

from bench import task

print("the circuit:", task.ghz_ops(3))
print("the ideal:  ", task.ideal_distribution(3))
print()

good = {"000": 2010, "111": 2050, "001": 20, "110": 16}
bad = {"000": 1200, "111": 2100, "001": 300, "010": 300, "100": 196}
for name, counts in (("a good run", good), ("a poor run", bad)):
    print(f"{name}: {counts}")
    print(f"  total variation {task.total_variation(counts, task.ideal_distribution(3)):.4f}, "
          f"signal {task.signal(counts):.4f}, "
          f"hellinger {task.hellinger(counts, task.ideal_distribution(3)):.4f}")
print()
print("the machine-built floor at 4,096 shots is 0.0098: an exact sampler cannot do")
print("better than the shot noise, so a smaller number is not a better machine.")
print()
print("three metrics on the same two runs, and they order them the same way:")
for name, counts in (("good", good), ("bad", bad)):
    tvd = task.total_variation(counts, task.ideal_distribution(3))
    hel = task.hellinger(counts, task.ideal_distribution(3))
    print(f"  {name}: tvd {tvd:.4f}, hellinger {hel:.4f}")
