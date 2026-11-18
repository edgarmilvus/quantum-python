"""Demo 01: nineteen contracts, read as a table.

Run: python3 chapters/chapter20/files/01_chapters.py

Every claim in chapters 1 to 19 has a contract: a floor, a harness count, an exercise
count, and the files it publishes. The ledger reads the contracts and prints them, and the
star marks the one that resolves its counts from a run rather than from the spec.
"""

from ledger import chapters, chapter_table

found = chapters()
print(chapter_table(found))
print()
print(f"{len(found)} chapters, {sum(c.proofs for c in found)} assertions, "
      f"{sum(c.artifacts for c in found)} files")
print(f"floor met by every chapter: {all(c.proofs > 0 and c.floor == 14000 for c in found)}")
print(f"counts taken from a record rather than a spec: {[c.number for c in found if c.from_record]}")
print()
print("the star is not a defect in the ledger: chapter 2's spec still carries the")
print("placeholder NN/NN, and its local run is the only place the real counts live.")
print("A closing chapter that hid that would be a summary, not an audit.")
