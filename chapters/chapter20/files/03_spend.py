"""Demo 03: the bill, and the invoice the pipeline refused.

Run: python3 chapters/chapter20/files/03_spend.py

Nineteen chapters, forty runs, 588,176 shots: paid, zero dollars. The zero is not a
rounding error, and the ledger refuses to print it for a provider it cannot price. Beside
it sits the 984.84 that chapter 19's estimate declined, which is the number that makes the
zero mean something.
"""

from ledger import refused_quote, spend_book

total = spend_book()
print(total.report())
print()
print(f"per proof:   {total.usd / total.proofs:.4f} USD")
print(f"per chapter: {total.words / total.chapters:.0f} words, {total.proofs / total.chapters:.0f} assertions")
print(f"per live run: {total.live_shots / total.live:.0f} shots")
print()
print(f"the refused invoice, recomputed: {refused_quote():.2f} USD")
print("six circuits at 2,048 shots on IonQ, which is 197 times chapter 19's budget.")
print()
print("a book that spent nothing is not a book that risked nothing: the runs are")
print("real, the job ids are in the record, and the refusal is a decision with a price.")
