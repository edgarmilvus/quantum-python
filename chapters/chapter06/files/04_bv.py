"""Demo 04: Bernstein-Vazirani, one query per bit of the secret.

Run: python3 chapters/chapter06/files/04_bv.py
"""

from algorithms import bernstein_vazirani, classical_queries_bernstein_vazirani, most_likely

print(f"{'n':>2s}{'secret':>8s}{'returned':>10s}{'P(returned)':>13s}{'classical queries':>18s}")
for n in (1, 2, 3, 4):
    for secret in (1, 3, 5):
        if secret >= (1 << n):
            continue
        distribution = bernstein_vazirani(secret, n)
        label, probability = most_likely(distribution)
        print(f"{n:2d}{format(secret, f'0{n}b'):>8s}{label:>10s}{probability:13.4f}"
              f"{classical_queries_bernstein_vazirani(secret, n):18d}")

print()
print("the returned string is the secret, and it comes back with probability one")
print("the classical program needs one query per bit: query 1, 2, 4, ... and read the answers")
