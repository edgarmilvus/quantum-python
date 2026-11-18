"""Demo 04: reads, milliseconds, and the arithmetic that connects them.

Run: python3 chapters/chapter14/files/04_reads.py

An anneal is short. The anneal time is a programmable quantity on the order of
twenty microseconds, so a thousand reads cost twenty milliseconds of machine time
and the expensive part is not the machine, it is the number of reads a success
probability forces. At p = 0.05 that number is fifty-nine for one success at 95%.
"""

from anneal import instances, sampler

coupling = instances.spin_glass()
exact = sampler.Exact({}, coupling).sample()
optimum = exact.best()[0]

print(f"{'sweeps':>7s}{'p(optimal)':>12s}{'reads 95%':>11s}{'reads 99%':>11s}{'milliseconds 95%':>18s}")
for sweeps in (10, 25, 100, 300, 1000):
    result = sampler.Annealer({}, coupling, 0.0, sweeps=sweeps, seed=11).sample(400)
    probability = sampler.success_rate(result, optimum)
    reads = sampler.reads_for(probability)
    reads99 = sampler.reads_for(probability, 0.99)
    milliseconds = reads * 0.020
    print(f"{sweeps:7d}{probability:12.3f}{reads:11d}{reads99:11d}{milliseconds:18.3f}")
print()
print("the anneal is 20 microseconds, which is the only machine number here")
print("that would come from the hardware; the record of a real machine would")
print("replace it with the measured anneal time and the programming time.")
print()

print(f"{'p per read':>11s}{'reads':>7s}{'machine time':>14s}")
for probability in (0.9, 0.5, 0.25, 0.1, 0.05, 0.01):
    reads = sampler.reads_for(probability)
    print(f"{probability:11.2f}{reads:7d}{reads * 0.020:12.3f} ms")
print()

print("for scale: one QAOA circuit on the account in chapter 13 took 0.33 seconds")
print("of runtime. One anneal is 20 microseconds of machine time, which is 16,500")
print("times shorter, and the two numbers measure different things: the first is a")
print("circuit plus the queue, the second is a scheduled annealing window.")
print()
print("what does not shrink is the reads: a machine that succeeds one time in")
print("twenty needs sixty attempts, and sixty attempts is the algorithm's cost.")
