"""Demo 03: the whole algorithm on 15, 21 and 35.

Run: python3 chapters/chapter09/files/03_shor.py
"""

import order

print("N = 15, a = 7, four bits and six ancillas:")
values = order.order_finding(7, 15, 4, 6)
for k, probability in sorted(values.items(), key=lambda item: -item[1])[:4]:
    result = order.attempt(7, 15, k, 6)
    print(f"  k={k:3d}  P={probability:.4f}  continued fraction -> r={result['r']:2d}  "
          f"factors={result['factors']}")
print()

for n, a, bits, ancillas in ((15, 7, 4, 6), (21, 2, 5, 8), (35, 2, 6, 10)):
    for candidate in (a,):
        success = order.quantum_success(candidate, n, bits, ancillas)
        classical = order.best_effort(n, list(range(2, n)))
        print(f"N={n:2d} a={candidate}: one run succeeds {success['probability']:.4f} of the time "
              f"from {int(success['outcomes'])} outcomes")
        print(f"   the classical half from the true order gives {order.shor(n, candidate)['factors']}; "
              f"the first working a is {classical['a']} after {classical['attempts']} attempts")

print()
print("a single run is a coin flip, so a real implementation repeats until the gcds work")
print("the number of attempts is geometric with the measured probability")
