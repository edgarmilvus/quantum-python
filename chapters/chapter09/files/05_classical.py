"""Demo 05: factoring without a quantum computer, and when it wins.

Run: python3 chapters/chapter09/files/05_classical.py

Trial division costs sqrt(N) divisions; Shor's classical half costs one order and two
gcds once the quantum machine has produced r. The table is the honest comparison.
"""

import math
import time

import order


def trial_division(n: int):
    if n < 2:
        raise ValueError(f"n must be at least two, got {n}")
    factor = 2
    while factor * factor <= n:
        if n % factor == 0:
            return factor, n // factor
        factor += 1
    return n, 1


def trial_count(n: int) -> int:
    factor = 2
    steps = 0
    while factor * factor <= n:
        steps += 1
        if n % factor == 0:
            return steps
        factor += 1
    return steps


def main() -> None:
    print(f"{'N':>10s}{'trial divisions':>18s}{'order':>8s}{'gcds':>6s}{'trial time':>13s}")
    for n in (15, 91, 1001, 10403, 1_000_003):
        start = time.perf_counter()
        trial_division(n)
        elapsed = (time.perf_counter() - start) * 1e3
        a = 2
        while math.gcd(a, n) != 1:
            a += 1
        r = order.order_of(a, n, limit=10_000_000)
        print(f"{n:10d}{trial_count(n):18d}{(r or 0):8d}{2:6d}{elapsed:12.2f} ms")

    print()
    print("the order is found by a classical loop here, which is the very thing Shor speeds up")
    print("the two gcds at the end cost microseconds and are not the bottleneck")
    print()
    print("so the honest claim: Shor does not replace trial division for small N, and")
    print("for large N the quantum machine does not exist at the size the estimate needs")


if __name__ == "__main__":
    main()
