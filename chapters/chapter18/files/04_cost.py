"""Demo 04: what each row costs, and what the same job would cost on a paid QPU.

Run: python3 chapters/chapter18/files/04_cost.py

Two of the three providers in the book are free at this scale; the third is not,
and its price is the reason the chapter exists. The table quotes a 4,096-shot GHZ
job on every provider chapter 11 lists, including the ones that were never run.
"""

from bench import sources, task

print("what one 4,096-shot job would cost, from chapter 11's price table:")
for provider in ("local", "qbraid", "ibm", "braket-iqm", "ionq"):
    price = sources.quoted(provider, 4096)
    print(f"  {provider:12s}{price:9.2f} USD")
print()
print("the book's own runs cost nothing because two of the three are free and the")
print("third was on an open plan that bills runtime. A reader who wants the same")
print("numbers on a paid QPU pays the last line.")
print()

rows = sources.ibm_ghz() + [sources.qbraid_ghz(), sources.local_ghz()]
print(f"{'source':26s}{'tvd':>8s}{'wall s':>9s}{'usd':>8s}{'usd per 0.01 tvd':>19s}")
for row in rows:
    per_point = row.cost_usd / max(row.tvd, 1e-9) * 0.01
    print(f"{row.source:26s}{row.tvd:8.4f}{row.wall_seconds:9.2f}{row.cost_usd:8.2f}{per_point:19.2f}")
print()
print("the last column is the only one that matters to a buyer, and it is zero for")
print("every row because none of them was paid for. The paid row's number is the")
print("one to compute before running the experiment, not after.")
