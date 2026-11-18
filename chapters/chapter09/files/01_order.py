"""Demo 01: the order of a modulo N, and the cycle it makes.

Run: python3 chapters/chapter09/files/01_order.py
"""

import order

for n in (15, 21, 35):
    print(f"N = {n}")
    for a in range(2, min(n, 13)):
        if __import__("math").gcd(a, n) != 1:
            continue
        r = order.order_of(a, n)
        cycle = []
        value = 1
        for _ in range(r):
            cycle.append(value)
            value = (value * a) % n
        factors = order.factors_from_order(a, n, r) if r else None
        print(f"  a={a:2d}  r={r}  cycle={cycle}  factors={factors}")
    print()

print("the cycle always returns to 1, and its length divides the group's size")
print("a factor appears when r is even and a^(r/2) is neither 1 nor -1 modulo N")
