# Providers — the account checklist

Six keyed providers and three keyless frameworks. The book runs offline
without any of them; an account buys a recorded run on real hardware.

## Create these six

| # | Provider | Free tier | What it unlocks in the book | Env var |
| --- | --- | --- | --- | --- |
| 1 | [IBM Quantum Platform](https://quantum.cloud.ibm.com) | Open Plan: 10 min QPU runtime per 28 days | The main real-QPU spine: Bell/CHSH, Grover, VQE, QAOA, surface-code experiments | `QISKIT_IBM_TOKEN`, `QISKIT_IBM_INSTANCE` |
| 2 | [IonQ Quantum Cloud](https://cloud.ionq.com) | Free account; simulators up to 29 qubits free | Trapped-ion native gates, all-to-all connectivity, a second hardware architecture | `IONQ_API_KEY` |
| 3 | [Amazon Braket](https://console.aws.amazon.com/braket) | 1 h/month on-demand simulator, first 12 months | One SDK, five vendors: Rigetti, IQM, AQT, QuEra, Pasqal — plus SV1/DM1/TN1 | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AMZN_BRAKET_OUT_S3_BUCKET` |
| 4 | [Azure Quantum](https://portal.azure.com) | New-account credits, plus per-provider quantum credits | Quantinuum (highest-fidelity ions) and Rigetti without a direct contract | `AZURE_QUANTUM_SUBSCRIPTION_ID`, `..._RESOURCE_GROUP`, `..._WORKSPACE` |
| 5 | [D-Wave Leap](https://cloud.dwavesys.com/leap) | Trial: dashboard demos only — **no API token since 2026** | Annealing taught with local `dimod` + `neal`; the prose never claims a QPU ran | `DWAVE_API_TOKEN` (unset) |
| 6 | [Quantum Inspire](https://compute.quantum-inspire.com) (QuTech) | Free account, real hardware included | A European academic QPU for the small circuits; the "free forever" comparison | `QUANTUM_INSPIRE_EMAIL` (QI 2.0 has no token; `qi login` authenticates once) |

## No account needed

| Framework | Why it is in the book |
| --- | --- |
| **Qiskit** | Local state-vector simulation, the reference implementation for most chapters |
| **NumPy** | The book's own matrices and local models, chapters 1-3 and the replay backends |
| **Cirq** | Optional second circuit model in chapter 2's ordering comparison; the chapter skips it when it is not installed |

## Optional, only if a chapter needs it

| Provider | Status | Verdict |
| --- | --- | --- |
| qBraid | Free account: free simulators, credits on request, one key for IonQ/Rigetti/IQM/AQT | **Used**: the seventh provider of chapter 11, recorded as run 0025 on its free simulator |
| Classiq | Free community tier | Acquired by Intel (Oct 2026); pricing may move. Mention, do not depend |
| Strangeworks | Credits through partner programs | Skip unless a reader asks |
| Google Quantum AI | Hardware access by application through a sponsor | No self-serve key. Use Cirq/qsim only |

## Cost rules for the book

- Hardware runs are **recorded**, never re-executed by the test suite.
- Chapter 11's registry refuses to submit when `QUANTUM_LIVE=0`, and the budget guard
  enforces `QUANTUM_MAX_SPEND_USD` (five dollars by default).
- The free tiers carried every run in the book: IBM's ten minutes per 28 days, IonQ's
  simulator, Quantum Inspire's emulator and qBraid's free simulators.
- The one invoice the book refused was 984.84 USD for six circuits at 2,048 shots on
  IonQ; chapter 19's estimate says no before the job exists.

## Verification, once keys exist

```bash
python3 live_scripts/check_providers.py --check      # prints which providers answer
python3 live_scripts/check_providers.py --budget     # remaining free time/credits, where reported
```

Nothing in the book's gates calls this. It exists so a reader can see what
their account actually gives them before spending it.
