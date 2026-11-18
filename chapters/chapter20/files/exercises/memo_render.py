"""Exercise 5, file 2 of 3: rendering the memo.

One title, six rows, one sentence, and a decision tally. A memo is read on a phone, so
the table has two columns and the sentence comes last.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


def rows(memo: Dict) -> List[Tuple[str, str]]:
    return [
        ("chapters", f"{memo['chapters']}"),
        ("runs", f"{memo['runs']} ({memo['live']} live)"),
        ("assertions", f"{memo['proofs']}"),
        ("words", f"{memo['words']}"),
        ("paid", f"{memo['usd']:.2f} USD"),
        ("refused", f"{memo['refused']:.2f} USD"),
    ]


def render(memo: Dict, sentence: str) -> str:
    if not memo.get("title"):
        raise ValueError("a memo needs a title")
    if not sentence:
        raise ValueError("a memo needs a sentence")
    decisions = ", ".join(f"{count} {name}" for name, count in memo["decisions"].items() if count)
    lines = [memo["title"], f"{'quantity':12s}{'value':>18s}"]
    for name, value in rows(memo):
        lines.append(f"{name:12s}{value:>18s}")
    lines.append(f"{'decisions':12s}{decisions:>18s}")
    lines.append("")
    lines.append(sentence)
    return "\n".join(lines) + "\n"
