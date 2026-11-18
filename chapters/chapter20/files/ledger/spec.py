"""The book's own records, read as data.

A closing chapter should not summarize from memory. The nineteen contracts in
`chapters/chapter*/spec.yaml` and the forty rows in `runs/INDEX.md` are files, and this
module turns them into two tuple types: a `Chapter` with its floors and its gate counts,
and a `Run` with its provider, its backend and its shots.

The parser is deliberately small: it reads the lines the ledger needs and refuses a spec
that does not have them. That is the same discipline as the pipeline's task, applied to
the book instead of to a circuit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[4]
CHAPTERS = ROOT / "chapters"
RUNS = ROOT / "runs"

# The book this chapter audits: chapters 1..19 and runs 0001..0040.
BOOK_CHAPTERS = 19
BOOK_RUNS = 40


@dataclass(frozen=True)
class Chapter:
    number: int
    title: str
    floor: int
    checks: int
    exercise_checks: int
    artifacts: int
    exercises: int
    from_record: bool = False

    @property
    def proofs(self) -> int:
        """The assertions a stranger can run: the harness plus the exercises."""
        return self.checks + self.exercise_checks

    def report(self) -> str:
        return (
            f"{self.number:2d}  {self.title:34s}{self.floor:7d}{self.proofs:8d}"
            f"{self.artifacts:8d}{self.exercises:6d}"
        )


@dataclass(frozen=True)
class Run:
    number: int
    case: str
    provider: str
    backend: str
    shots: int
    summary: str

    @property
    def live(self) -> bool:
        """A run is live when it left this machine; the local ones never did."""
        return not self.provider.startswith("local")

    def report(self) -> str:
        kind = "live" if self.live else "local"
        return f"{self.number:04d}  {kind:5s} {self.provider:34s}{self.shots:9d}  {self.case}"


def _scalar(text: str, key: str) -> str:
    match = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
    if not match:
        raise ValueError(f"a spec has no {key!r} line")
    return match.group(1).strip().strip('"')


def _count_block(text: str, key: str) -> int:
    """Count the list items under a top-level key, stopping at the next key."""
    inside = False
    count = 0
    for line in text.splitlines():
        if line.startswith(f"{key}:"):
            inside = True
            continue
        if inside:
            if line.startswith("  - "):
                count += 1
            elif line and not line.startswith(" "):
                break
    return count


def _fraction(pattern: str, text: str, what: str) -> int:
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"a spec has no {what} expectation")
    return int(match.group(1))


def _from_record(number: int, section: str) -> int:
    """Read a gate count from the chapter's own local run, when the spec cannot say it."""
    matches = sorted(RUNS.glob(f"*-chapter{number:02d}-local/output.txt"))
    if not matches:
        raise FileNotFoundError(f"chapter {number} has no local record under {RUNS}")
    case = matches[0]
    text = case.read_text()
    if f"== {section}" not in text:
        raise ValueError(f"{case} has no '== {section}' section")
    match = re.search(r"(\d+)/\d+", text.split(f"== {section}", 1)[1])
    if not match:
        raise ValueError(f"{case} has no count after '== {section}'")
    return int(match.group(1))


def read_chapter(path: Path) -> Chapter:
    text = path.read_text()
    floor = re.search(r"floor:\s*(\d+)", text)
    if not floor:
        raise ValueError(f"{path}: no words.floor")
    number = int(_scalar(text, "chapter"))
    fallback = bool(re.search(r'expected:\s*"NN/NN', text))
    checks = (
        _from_record(number, "harness")
        if fallback
        else _fraction(r'harness_expected:\s*"(\d+)/', text, "harness")
    )
    exercises = (
        _from_record(number, "exercises")
        if fallback
        else _fraction(r'exercises_expected:\s*"(\d+)/', text, "exercises")
    )
    return Chapter(
        number=number,
        title=_scalar(text, "title"),
        floor=int(floor.group(1)),
        checks=checks,
        exercise_checks=exercises,
        artifacts=_count_block(text, "artifacts"),
        exercises=_count_block(text, "exercises"),
        from_record=fallback,
    )


def chapters(through: int = BOOK_CHAPTERS) -> Tuple[Chapter, ...]:
    """Every contract up to and including `through`, in reading order."""
    found: List[Chapter] = []
    for spec in sorted(CHAPTERS.glob("chapter*/spec.yaml")):
        chapter = read_chapter(spec)
        if chapter.number <= through:
            found.append(chapter)
    return tuple(sorted(found, key=lambda chapter: chapter.number))


def _shots(cell: str) -> int:
    """Read a shot cell: '2048 x 6' is twelve thousand two hundred and eighty-eight."""
    many = re.search(r"(\d[\d,]*)\s*x\s*(\d+)", cell)
    if many:
        return int(many.group(1).replace(",", "")) * int(many.group(2))
    thousands = re.search(r"(\d+)\s*k\b", cell, re.IGNORECASE)
    if thousands:
        return int(thousands.group(1)) * 1000
    one = re.search(r"(\d[\d,]*)", cell)
    return int(one.group(1).replace(",", "")) if one else 0


def runs(through: int = BOOK_RUNS) -> Tuple[Run, ...]:
    """The index's table rows, parsed; a row is the only record every run has."""
    index = RUNS / "INDEX.md"
    if not index.exists():
        raise FileNotFoundError(f"no run index at {index}")
    found: List[Run] = []
    for line in index.read_text().splitlines():
        if not line.startswith("| 0"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            raise ValueError(f"a run row has {len(cells)} cells: {line[:60]!r}")
        number = int(cells[0])
        if number <= through:
            found.append(Run(number, cells[1], cells[2], cells[3], _shots(cells[4]), cells[5]))
    return tuple(found)


def words(chapter_id: str) -> int:
    """The chapter's word count, recorded beside its contract when the book was built."""
    path = CHAPTERS / chapter_id / "words.txt"
    if not path.exists():
        raise FileNotFoundError(f"no word count at {path}")
    return int(path.read_text().strip())
