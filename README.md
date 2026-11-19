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
own checks. Across the twenty chapters that is **2,629 assertions**, and the whole suite
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
| 20 | [The Last Experiment](chapters/chapter20/) | 126 | 20 |

Each chapter folder holds `spec.yaml` (the contract: floor, gate counts and files) and
`files/` with the code the chapter publishes. The prose itself is the book; this repository is what it runs. Every `**How to run it.**`
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
The suite covers 2,629 assertions, takes about a minute, and ends `all chapters green`:

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

Chapters 11 to 20 were recorded against real providers, and the records live under
`runs/chapterNN/<id>-<name>/`. Two different things can spend a job, and they are guarded
differently:

- **the chapter 11 interface** — `providers/registry.py` refuses to submit unless
  `QUANTUM_LIVE=1`, and its budget guard enforces `QUANTUM_MAX_SPEND_USD` (five dollars by
  default). The chapter's demos go through it.
- **the submit scripts under `live_scripts/`** — `submit_bv.py`, `submit_teleport.py` and
  the rest submit as soon as they are invoked. They read the keys from `.env` and do not
  check `QUANTUM_LIVE`; run them one at a time, on purpose.

Copy the environment file and fill in the keys you have:

```bash
cp .env.example .env
```

| variable | provider | what it enables |
| --- | --- | --- |
| `QISKIT_IBM_TOKEN`, `QISKIT_IBM_INSTANCE` | IBM Quantum | the device runs in chapters 4, 7, 13, 15, 16, 17, 18, 19, 20 |
| `QBRAID_API_KEY` | qBraid | the gateway to IonQ in chapters 11 and 18 |
| `IONQ_API_KEY` | IonQ | the simulator and device calls in chapter 11 |
| `QUANTUM_LIVE` | chapter 11 | `1` allows a submission through the interface; `0` replays |
| `QUANTUM_MAX_SPEND_USD` | chapter 11 | the interface's ceiling, five dollars by default |

The submit scripts, with the job each one sends and what it costs in QPU time (one second
of runtime is roughly 3,000 shots):

| script | re-records | job | QPU |
| --- | --- | --- | --- |
| `live_scripts/hello_ibm.py` | a smoke test | 1 × 1,024 | < 1 s |
| `live_scripts/hello_ionq.py` | a smoke test | 1 × 1,024 | free |
| `live_scripts/hello_qi.py` | a smoke test | 1 × 1,024 | free |
| `live_scripts/chapter04/submit_chsh.py` | chapter 4 | 4 × 1,024 | ~1.5 s |
| `live_scripts/chapter06/submit_bv.py` | chapter 6 | 1 × 1,024 | < 1 s |
| `live_scripts/chapter07/submit_grover.py` | chapter 7 | 1 × 1,024 | < 1 s |
| `live_scripts/chapter10/submit_vqe.py` | chapter 10 | 2 × 10,000 | ~7 s |
| `live_scripts/chapter12/submit_readout.py` | chapter 12 | 4 × 4,096 | ~5 s |
| `live_scripts/chapter13/submit_qaoa.py` | chapter 13 | 36 × 1,024 | ~12 s |
| `live_scripts/chapter15/submit_kernel.py` | chapter 15 | 57 × 1,024 | ~19 s |
| `live_scripts/chapter16/submit_repetition.py` | chapter 16 | 12 × 4,096 | ~16 s |
| `live_scripts/chapter16/submit_idle.py` | chapter 16 | 12 × 4,096 | ~16 s |
| `live_scripts/chapter17/submit_dynamic.py` | chapter 17 | 8 × 4,096 | ~11 s |
| `live_scripts/chapter17/submit_inject.py` | chapter 17 | 6 × 4,096 | ~8 s |
| `live_scripts/chapter17/submit_latency.py` | chapter 17 | 3 × 4,096 | ~4 s |
| `live_scripts/chapter17/submit_syndrome.py` | chapter 17 | 2 × 8,192 | ~5 s |
| `live_scripts/chapter18/submit_ghz.py` | chapter 18 | 2 × 4,096, plus qBraid | ~3 s |
| `live_scripts/chapter19/submit_bv_pipeline.py` | chapter 19 | 6 × 2,048 | ~4 s |
| `live_scripts/chapter20/submit_teleport.py` | chapter 20 | 13 × 2,048 | ~9 s |

A full pass is about two minutes of QPU and thirty to sixty minutes of wall clock, almost
all of it in the queue. Each script **overwrites** its record under `runs/chapterNN/`; the
harnesses assert the recorded numbers, so after an experiment either restore the tree with
`git checkout -- runs/` or work in a second clone.

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
  files/                    the listings, the demos, the harness
  files/exercises/          the five exercises, their checks and the runner
runs/chapterNN/<id>-<name>/  one recorded experiment: result.json or gate/output
runs/INDEX.md               the one row every run has
live_scripts/               provider check, hello scripts, one folder per chapter
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
