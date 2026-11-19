# Recorded runs

Every number the book quotes about real hardware comes from a file in this
directory. Nothing here is hand-written: `result.json` is written by the
program that submitted the job, or transcribed from its stdout in the same
commit as the program.

| # | case | provider | backend | shots | what it proves |
| --- | --- | --- | --- | --- | --- |
| 0001 | `ibm-fez-bell-1024` | IBM Quantum | ibm_fez (156q) | 1024 | Bell pair holds at 94.6% correlated; the 5.4% residue is readout bias |
| 0002 | `qi-qx-emulator-bell-1024` | Quantum Inspire | QX emulator (10q) | 1024 | 100% correlated on a noise-free emulator, the control for 0001; every free QPU was offline at submission |
| 0003 | `ionq-simulator-bell` | IonQ | simulator (ideal) | 1024 | Probabilities 0.5 / 0.5 on \|00⟩ and \|11⟩; the API returns probabilities, not counts, so `shots` is ignored |
| 0004 | `chapter01-local` | local simulators | numpy, Qiskit, PennyLane, Cirq | 1000 | The chapter's gate: 91/91 harness checks, 52/52 exercise checks, 4 implementations at zero distance, float32 failing at cycle 2020 |
| 0005 | `chapter02-local` | local simulators | numpy, Qiskit, PennyLane, Cirq | 2000 | 80/80 checks, 55/55 exercises; Qiskit and this chapter differ by exactly 1.0 before the endianness conversion and 0.0 after |
| 0006 | `chapter03-local` | local simulators + recorded ibm_fez profile | numpy, Qiskit (comparison only) | 1024 (reused) | 73/73 checks, 56/56 exercises; Bell compiles 2→10 gates, depth 2→7, unitary distance 1.4e-16; device 0.0537 vs predicted 0.0668 |
| 0007 | `ibm-chsh` | IBM Quantum | ibm_fez (156q) | 1024 x 4 | CHSH on hardware: S = 2.541 +/- 0.048, 11.2 sigma over the classical bound, 65% of the ideal violation |
| 0008 | `chapter04-local` | local simulators | numpy | 200k (model) | 49/49 checks, 53/53 exercises; ideal S = 2.828427, local model 2.0012 +/- 0.0039 |
| 0009 | `ibm-readout` | IBM Quantum | ibm_fez (156q) | 4096 x 4 | Readout calibration: diagonal 0.979/0.953/0.962/0.932, average error 4.34%, determinant 0.836 |
| 0019 | `chapter11-local` | local + IonQ simulator (one live call) | providers | 512 (live) | 44/44 checks, 48/48 exercises; live IonQ gives {00: 0.5, 11: 0.5}, replay of 0001 gives four outcomes |
| 0017 | `ibm-vqe` | IBM Quantum | ibm_fez (156q) | 10000 x 2 | VQE H2 at theta -0.2235, depth 9: -1.050342 +/- 0.0025, 87 mHa above exact; mitigation gives -1.0745 |
| 0018 | `chapter10-local` | local | numpy | -- | 50/50 checks, 56/56 exercises; exact -1.137305, HF -1.116998, sigma 7.89 mHa at 1k shots |
| 0016 | `chapter09-local` | local | numpy | -- | 44/44 checks, 130/130 exercises; Shor at 15 succeeds 0.5/run, 21 gives 0.2856, 35 gives 0.2992; 2048 needs 36 qubits and 1 TiB |
| 0015 | `chapter08-local` | local | numpy | -- | 80/80 checks, 65/65 exercises; PEA exact 1.0, 1/3 at 4 bits 0.6849, worst case 0.4118 vs 4/pi^2 |
| 0013 | `ibm-grover` | IBM Quantum | ibm_fez (156q) | 1024 | Grover, 3 qubits, marked 101, 2 iterations: 732/1024 = 71.5% vs ideal 94.5%, depth 169 |
| 0014 | `chapter07-local` | local simulators | numpy | -- | 52/52 checks, 59/59 exercises; curve 0.125/0.781/0.945/0.330/0.012, optimum exact vs approximate |
| 0011 | `ibm-bv` | IBM Quantum | ibm_marrakesh (156q) | 1024 | Bernstein-Vazirani, secret 101: 965/1024 = 94.2%, depth 9, five outcomes seen |
| 0012 | `chapter06-local` | local simulators | numpy | -- | 131/131 checks, 75/75 exercises; DJ and BV exact at 1.0, promise table 8/16 correct |
| 0010 | `chapter05-local` | local | numpy | -- | 52/52 checks, 48/48 exercises; correcting with the matrix takes CHSH S from 2.541 to 2.780 |
| 0020 | `ibm-fez-calibration` | IBM Quantum (saved snapshot) | ibm_fez (156q) | -- | Exported once: Grover transpiles to depth 169 and 45 two-qubit gates, exactly as run 0013 recorded; 176 edges, median CZ 0.0039, max 1.0 (a dead coupler) |
| 0021 | `chapter12-local` | local | numpy | 4096 (model) | 95/95 checks, 85/85 exercises; per-gate model predicts Grover 0.7779 against 0.7649 measured (1.0 sigma); ZNE recovers 2.8260 against 2.8284, raw ZNE only 2.5812 |
| 0022 | `ibm-fez-qaoa` | IBM Quantum | ibm_marrakesh (156q) | 1024 x 36 | QAOA p=1 landscape on MaxCut(4 vertices, 5 edges), depth 76, 12 s of runtime: best grid point (0.3142, 0.6283) at 3.1006 of 4, r = 0.9918 against the simulator, slope 0.827 through the uniform mean 2.5 |
| 0023 | `chapter13-local` | local | numpy | 1024 (model) | 73/73 checks, 89/89 exercises; p=1 3.2371 (0.8093), p=2 3.8558, p=3 3.9870, p=4 3.9994; one gradient is 12 circuits, twenty steps 240 |
| 0024 | `chapter14-local` | local | numpy | 200 (model) | 63/63 checks, 75/75 exercises; K12 spin glass optimum -24 found 76.5% at 10 sweeps and 99% at 300; chain strength 0.2 breaks 19.2% and 1.0 breaks none; no QPU, no token in 2026 |
| 0025 | `qbraid-bell` | qBraid (aggregator) | qbraid:qbraid:sim:qir-sv (30q) | 1024 | First qBraid job, through chapter 11's own adapter: {00: 509, 11: 515}, cost 0 credits, 37 ms; the seventh provider is the aggregator, and this is the evidence the interface reaches it |
| 0026 | `ibm-fez-kernel` | IBM Quantum | ibm_fez (156q) | 1024 x 57 | Quantum kernel on a 12-point spiral, reps=3, depth 66: diagonal 0.9827, off-diagonal correlation 0.817 with the exact matrix, one pair 0.683 -> 0.239, accuracy 0.833 against 1.000 exact and 0.667 classical |
| 0027 | `chapter15-local` | local | numpy | 1024 (model) | 52/52 checks, 72/72 exercises; reps 1..4 give 0.333/0.667/1.000/0.833, exact kernel 1.000 at every penalty, 57 circuits for 6+6 points |
| 0028 | `ibm-fez-repetition` | IBM Quantum | ibm_kingston (156q) | 4096 x 12 | Repetition code, zero idle: d=3 at 2.44% physical gives 0.15% logical, d=5 gives zero in 4,096 shots |
| 0029 | `ibm-fez-idle` | IBM Quantum | ibm_marrakesh (156q) | 4096 x 12 | Idle 0/20/60 us: d=3 logical 0.0012/0.0369/0.1628, d=5 0.0000/0.0156/0.1387; binomial predicts all six decaying rows within 0.0024 |
| 0030 | `chapter16-local` | local | numpy | 20000 (model) | 48/48 checks, 85/85 exercises; binomial 0.00725/0.00116/0.00019 at p=0.05; phase axis 0.1355/0.2048/0.2609 |
| 0031 | `ibm-fez-dynamic` | IBM Quantum | ibm_marrakesh (156q) | 4096 x 8 | In-circuit correction vs control: clean codeword 0.0325 against 0.0005, so correction loses; the syndrome is the reason |
| 0032 | `ibm-fez-inject` | IBM Quantum | ibm_marrakesh (156q) | 4096 x 6 | One injected flip: codeword clean 0.810/0.904/0.813 with correction against 0.026/0.010/0.026 without |
| 0033 | `ibm-fez-latency` | IBM Quantum | ibm_marrakesh (156q) | 4096 x 3 | No conditional 0.0010, conditional with identity 0.0005, conditional with X 0.0237: the round trip is free |
| 0034 | `ibm-fez-syndrome` | IBM Quantum | ibm_kingston (156q) | 8192 x 2 | Both registers returned: clean 111 gives syndrome 00 93.7%, false 6.3%, against a 1.9% data error |
| 0035 | `chapter17-local` | local | numpy | 400 (model) | 38/38 checks, 60/60 exercises; trajectories repair every single flip and none of the doubles |
| 0036 | `ibm-fez-ghz` | IBM Quantum | ibm_kingston (156q) | 4096 x 2 | GHZ-3 at 4,096 shots: TVD 0.0681 at zero delay, 0.1616 at 20 us; 4 s of runtime, 160.7 s of wall clock |
| 0037 | `qbraid-ghz` | qBraid (gateway to IonQ) | ionq:ionq:sim:simulator | 4096 | GHZ-3 through the gateway: TVD 0.0000 because the simulator returns probabilities, 11.6 s wall, 0 credits |
| 0038 | `chapter18-local` | local | numpy | 4096 (model) | 44/44 checks, 68/68 exercises; floor 0.0229/0.0123/0.0069/0.0028 at 256/1,024/4,096/16,384 shots |
| 0039 | `ibm-fez-pipeline` | IBM Quantum | ibm_fez (156q) | 2048 x 6 | BV-4 with secret 1011 in one job with five calibration circuits: raw 0.9551, corrected 0.9880, depth 10, 4 s of runtime; worst readout 4.88% |
| 0040 | `chapter19-local` | local | numpy | 2048 (record) | 42/42 checks, 71/71 exercises; inverse on the left 0.9880 against the transpose's 0.9732; determinant 0.2357, condition number 1.22 |
| 0041 | `chapter20-local` | local | numpy | -- | 63/63 checks, 75/75 exercises; the ledger reads 19 contracts and 40 runs: 2,503 assertions, 588,176 shots, 0.00 USD paid against 984.84 refused; no device job |
| 0042 | `ibm-fez-teleport` | IBM Quantum | ibm_kingston (156q) | 2048 x 13 | Teleportation with theta=pi/3, phi=pi/4: dynamic 0.9558, postselect 0.9499, uncorrected 0.4858; readout 0.20%/2.93%; depth 18, one job |

## Conventions

- One directory per experiment: `runs/chapterNN/<NNNN>-<name>/`. The four digits
  are the stable citation the prose uses; the rest of the name says what ran and at how
  many shots.
- `result.json` holds the raw counts and the metadata needed to re-read them:
  provider, backend, job id, shots, circuit depth before and after transpilation.
- `derived` holds only arithmetic done on `counts`, so a reader can recompute it.
- A run is never edited. A re-run gets a new directory, and the prose names
  which one it quotes.
- Credentials never appear here. Job ids are public to the account holder only,
  and they are kept because they are the proof the job existed.
