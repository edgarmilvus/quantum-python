"""Demo 06: the same ordering defect, in a CSV instead of a state vector.

A device export labels its columns in the order the vendor chose. Reading the
header as if it were your order mirrors every row. The defect is identical to the
one between Qiskit and Cirq, and it survives because the numbers are plausible.

Run: python3 chapters/chapter02/files/06_second_domain.py
"""

from __future__ import annotations

from typing import Dict, List, Tuple

EXPORT = """q1,q0,count
0,0,0
0,1,412
1,0,588
1,1,0
"""


def parse(text: str) -> Tuple[List[str], Dict[str, int]]:
    lines = [line for line in text.strip().splitlines() if line]
    header = lines[0].split(",")[:-1]
    counts = {}
    for line in lines[1:]:
        parts = line.split(",")
        bits, count = parts[:-1], int(parts[-1])
        # The key is built in the order the header declares.
        counts["".join(bits)] = count
    return header, counts


def relabel(counts: Dict[str, int], header: List[str], wanted: List[str]) -> Dict[str, int]:
    """Re-key counts so the bits appear in `wanted` order."""
    if sorted(header) != sorted(wanted):
        raise ValueError(f"cannot reorder {header} into {wanted}")
    order = [header.index(name) for name in wanted]
    out = {}
    for key, count in counts.items():
        out["".join(key[i] for i in order)] = out.get("".join(key[i] for i in order), 0) + count
    return out


def main() -> None:
    header, counts = parse(EXPORT)
    print(f"header: {header}")
    print(f"as exported:  {dict(sorted(counts.items()))}")

    wanted = ["q0", "q1"]
    fixed = relabel(counts, header, wanted)
    print(f"as {wanted}:     {dict(sorted(fixed.items()))}")
    print()
    print("the rows that look populated change:")
    for name, table in (("exported", counts), ("relabelled", fixed)):
        hot = [key for key, value in table.items() if value > 0]
        print(f"  {name:12s} {hot}")
    print()
    print("total shots:", sum(counts.values()))
    print("totals agree:", sum(counts.values()) == sum(fixed.values()))

    try:
        relabel(counts, header, ["q0"])
    except ValueError as exc:
        print(f"refused: {exc}")


if __name__ == "__main__":
    main()
