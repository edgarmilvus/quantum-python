"""The ledger's three tables: chapters, providers, decisions.

A closing report is read once, so it has to be printed well: one line per row, the
number that matters on the right, and no column that a reader has to decode. The
functions here are presentation only, and that is deliberate — every number they print
was computed in `spec`, `spend` or `decide`.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from . import decide, spec, spend


def chapter_table(chapters: Sequence[spec.Chapter]) -> str:
    width = max(len(chapter.title) for chapter in chapters) + 2
    lines = [f"{'#':>2s}  {'chapter':{width}s}{'floor':>7s}{'proofs':>8s}{'files':>7s}{'ex':>4s}"]
    for chapter in chapters:
        mark = "*" if chapter.from_record else " "
        lines.append(
            f"{chapter.number:2d}  {chapter.title + mark:{width}s}{chapter.floor:7d}"
            f"{chapter.proofs:8d}{chapter.artifacts:7d}{chapter.exercises:4d}"
        )
    return "\n".join(lines)


def provider_table(runs: Sequence[spec.Run]) -> str:
    totals: Dict[str, List[int]] = {}
    for run in runs:
        row = totals.setdefault(run.provider, [0, 0])
        row[0] += 1
        row[1] += run.shots
    width = max(len(name) for name in totals) + 2
    lines = [f"{'provider':{width}s}{'runs':>6s}{'shots':>10s}"]
    for name, (count, shots) in sorted(totals.items(), key=lambda pair: (-pair[1][1], pair[0])):
        lines.append(f"{name:{width}s}{count:6d}{shots:10d}")
    return "\n".join(lines)


def decision_table(verdicts: Sequence[decide.Verdict]) -> str:
    width = max(len(verdict.problem) for verdict in verdicts) + 2
    lines = [f"{'problem':{width}s}{'decision':>10s}{'USD':>9s}   reason"]
    for verdict in verdicts:
        lines.append(f"{verdict.problem:{width}s}{verdict.decision:>10s}{verdict.usd:9.2f}   {verdict.reason}")
    return "\n".join(lines)


def counts(verdicts: Sequence[decide.Verdict]) -> Tuple[Tuple[str, int], ...]:
    """How many of each decision, in the order the chapter presents them."""
    order = ("device", "skip", "wait", "simulate", "refuse")
    return tuple((name, sum(1 for verdict in verdicts if verdict.decision == name)) for name in order)


def summary(total: spend.Spend, verdicts: Sequence[decide.Verdict]) -> str:
    tally = ", ".join(f"{count} {name}" for name, count in counts(verdicts))
    return (
        "Quantum Python, chapters 1-19\n"
        f"  chapters   {total.chapters}\n"
        f"  runs       {total.runs} ({total.live} live, {total.local} local)\n"
        f"  shots      {total.shots}\n"
        f"  proofs     {total.proofs}\n"
        f"  words      {total.words}\n"
        f"  artifacts  {total.artifacts}\n"
        f"  paid       {total.usd:.2f} USD\n"
        f"  refused    {spend.refused_quote():.2f} USD\n"
        f"  decisions  {tally}"
    )
