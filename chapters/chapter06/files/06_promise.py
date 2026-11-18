"""Demo 06: what happens when the promise is dropped.

Deutsch-Jozsa is a promise problem: the function is guaranteed constant or balanced.
Every function of two bits is enumerated here, and the algorithm is asked for an answer
anyway. It returns one of two labels for all sixteen, and eight of them are neither.

Run: python3 chapters/chapter06/files/06_promise.py
"""

from algorithms import deutsch_jozsa, deutsch_jozsa_answer
from oracle import is_balanced

N = 2


def truth(value: int) -> list:
    return [(value >> x) & 1 for x in range(1 << N)]


counts = {"constant": 0, "balanced": 0, "neither": 0}
correct = 0
table = []

for value in range(1 << (1 << N)):
    f = lambda x, v=value: (v >> x) & 1
    answers = {f(x) for x in range(1 << N)}
    if len(answers) == 1:
        truth_label = "constant"
    elif answers == {0, 1} and sum(truth(value)) == (1 << N) // 2:
        truth_label = "balanced"
    else:
        truth_label = "neither"
    counts[truth_label] += 1
    answer = deutsch_jozsa_answer(deutsch_jozsa(f, N))
    table.append((format(value, f"0{1 << N}b"), truth_label, answer, answer == truth_label))
    if answer == truth_label:
        correct += 1

print(f"all {1 << (1 << N)} functions of {N} bits: {counts}")
print(f"the algorithm labels {correct} of them correctly, all of them constant or balanced")
print()
print(f"{'truth table':12s}{'really':10s}{'answer':10s}{'right':>7s}")
for bits, truth_label, answer, right in table[:8]:
    print(f"{bits:12s}{truth_label:10s}{answer:10s}{str(right):>7s}")
print("...")
print()
print("eight functions are neither, and the algorithm still answers: that is the promise")
print("without it, the single query carries no information about the question being asked")
