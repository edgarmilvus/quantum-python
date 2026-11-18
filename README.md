# Quantum Python — sources, code, and the runs behind the book

The repository for *Quantum Python* by Edgar Milvus: twenty chapters that take a senior
software engineer from a complex amplitude to a priced, corrected, replayable pipeline,
with no physics assumed.

It holds one contract per chapter, the code each chapter publishes, the recorded runs the
prose quotes, and the scripts that rerun them. One command takes a fresh clone to a green
suite:

```bash
./run_offline.sh all          # or: python3 run_offline.py
```

Every chapter ships a harness that asserts on real numbers and five exercises with their
own checks. Across the twenty chapters that is **2,641 assertions**, and the whole suite
runs offline in about fifty seconds.

## The chapters

| # | chapter | assertions | files |
| --- | --- | --- | --- |
| 1 | [The Qubit Is a Vector](chapters/chapter01/) | 143 | 19 |
| 2 | [Two Qubits, and the Order That Bites](chapters/chapter02/) | 135 | 18 |
| 3 | [Circuits, Unitaries, Compilation](chapters/chapter03/) | 129 | 21 |
| 4 | [Entanglement and the CHSH Inequality](chapters/chapter04/) | 102 | 16 |
| 5 | [Shots, Statistics, Error Bars](chapters/chapter05/) | 100 | 18 |
| 6 | [Oracles: Deutsch-Jozsa and Bernstein-Vazirani](chapters/chapter06/) | 206 | 18 |
| 7 | [Grover and Amplitude Amplification](chapters/chapter07/) | 111 | 16 |
| 8 | [The Quantum Fourier Transform and Phase Estimation](chapters/chapter08/) | 145 | 17 |
| 9 | [Order Finding and Shor-lite](chapters/chapter09/) | 174 | 16 |
| 10 | [VQE for the Hydrogen Molecule](chapters/chapter10/) | 106 | 18 |
| 11 | [One Interface, Seven Providers](chapters/chapter11/) | 93 | 23 |
| 12 | [Noise and Error Mitigation](chapters/chapter12/) | 180 | 23 |
| 13 | [QAOA and Combinatorial Optimization](chapters/chapter13/) | 162 | 21 |
| 14 | [Annealing and the D-Wave Problem](chapters/chapter14/) | 138 | 20 |
| 15 | [Quantum Machine Learning](chapters/chapter15/) | 123 | 20 |
| 16 | [Error Correction](chapters/chapter16/) | 133 | 18 |
| 17 | [Dynamic Circuits](chapters/chapter17/) | 98 | 18 |
| 18 | [The Benchmark](chapters/chapter18/) | 112 | 18 |
| 19 | [The Pipeline](chapters/chapter19/) | 113 | 19 |
| 20 | [What to Do on Monday](chapters/chapter20/) | 138 | 20 |

Each chapter folder holds `spec.yaml` (the contract: floor, gate counts and files),
`words.txt` (the chapter's length, recorded when the book was built), and `files/` with the
code the chapter publishes. The prose itself is the book; this repository is what it runs. Every `**How to run it.**`
block in the prose names the file it belongs to, and the listing in the book is the file
byte for byte.

## Setup

Python 3.11 or 3.12.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```


## Run offline

The whole book, no key and no network:

```bash
./run_offline.sh all
```

or, without a POSIX shell:

```bash
python3 run_offline.py
```

Both walk the chapters in order and run each chapter's harness, then its five exercises.
The suite covers 2,641 assertions, takes about a minute, and ends `all chapters green`:

```
== chapter20
63/63 checks passed
75/75 exercise checks passed
...
all chapters green
``` One chapter, while
you are working on it:

```bash
./run_offline.sh chapter18
python3 run_offline.py chapter18
```

One chapter's code without any runner:

```bash
cd chapters/chapter20/files
python3 05_report.py
```

## Live run

Chapters 11 to 19 were recorded against real providers, and their records live under
`runs/`. To submit a job yourself, copy the environment file and fill in the keys you
have:

```bash
cp .env.example .env
```

| variable | provider | what it enables |
| --- | --- | --- |
| `QISKIT_IBM_TOKEN` | IBM Quantum | the device runs in chapters 4, 7, 13, 15, 16, 17, 18, 19 |
| `QBRAID_API_KEY` | qBraid | the gateway to IonQ in chapters 11 and 18 |
| `IONQ_API_KEY` | IonQ | the simulator and device calls in chapter 11 |
| `QUANTUM_LIVE` | all | `1` allows a submission; `0` replays the record |
| `QUANTUM_MAX_SPEND_USD` | all | the guard's ceiling, five dollars by default |

With `QUANTUM_LIVE=0`, every script reads the recorded run and prints the same answer
without a network. With `QUANTUM_LIVE=1` and a key, the scripts that say so submit:

```bash
python3 tools/run_pipeline.py      # chapter 19: six circuits, about four seconds of IBM runtime
python3 tools/run_benchmark.py     # chapter 18: GHZ on IBM and through qBraid
python3 tools/hello_ibm.py         # the smallest possible job
```

The book spent **0.00 USD**: every provider it used was a free tier. The IBM open plan
gives ten minutes of QPU time per 28 days, which is the real budget; qBraid and IonQ's
simulator were free. D-Wave had no trial token in 2026, so chapter 14 runs on local
simulators and says so rather than borrowing a number. A paid job is a choice the estimate
in chapter 19 prices before it is submitted, and it refused the one quote in the book:
984.84 USD for six circuits at 2,048 shots.

## Windows

Native Windows works; there is no WSL step.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

.venv\Scripts\python run_offline.py
.venv\Scripts\python run_offline.py chapter20
```

`run_offline.sh` is a bash script; `run_offline.py` is its twin and takes the same
argument. The individual programs are plain Python and run the same way:

```powershell
cd chapters\chapter20\files
..\..\..\.venv\Scripts\python 05_report.py
```

Paths in the code come from `pathlib`, so a run writes `chapters\chapter20\...` where the
book shows `chapters/chapter20/...`; that is the only difference.

## Layout

```
chapters/chapterNN/
  spec.yaml                 the contract: floor, gate counts, artifacts, exercises
  words.txt                 the chapter's length, recorded when the book was built
  files/                    the listings, the demos, the harness
  files/exercises/          the five exercises, their checks and the runner
runs/NNNN-<case>/           one recorded run: result.json or gate/output
runs/INDEX.md               the one row every run has
tools/                      provider check, hello scripts, the recorded-run scripts
run_offline.sh              the suite, POSIX shell
run_offline.py              the same suite, shell-free
requirements.txt            the pinned stack
LICENSE                     MIT, for the code
LICENSE-BOOK.md             the book is © Edgar Milvus, all rights reserved
```

## Licence

The code in this repository is released under the **MIT License**; see `LICENSE`. Use it,
change it, ship it, including commercially, as long as the copyright notice travels with
it.

The **book is not MIT**: the text, the figures and the diagrams are © 2026 Edgar Milvus,
all rights reserved. Quoting a listing or a paragraph in a review or a course is fine;
redistributing the book is not. `LICENSE-BOOK.md` has the exact terms.

## When something does not start

| message | what it means |
| --- | --- |
| `ModuleNotFoundError: No module named 'qiskit'` | the virtual environment is not active, or `pip install -r requirements.txt` was never run in it |
| `no spec: chapters/chapter20/spec.yaml` | run the commands from the repository root, where the chapter globs resolve |
| `refused: 984.84 USD is over the 5.00 budget` | the pipeline working as designed: the estimate prices a job before it is submitted |
| `no key` in a live script | `.env` is missing or empty: copy `.env.example` and set the key for that provider |

## Checks

Each chapter's own files are the check: `chapters/chapterNN/files/run_exNN.py` asserts on
the chapter's numbers and exits non-zero when one is wrong, and
`chapters/chapterNN/files/exercises/run_exercises.py` runs the five exercises' checks.
`run_offline.sh` and `run_offline.py` are only a loop over those two files, so a chapter
that prints `NN/NN checks passed` and `NN/NN exercise checks passed` is green.
