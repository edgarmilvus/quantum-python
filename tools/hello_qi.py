"""Minimal Quantum Inspire check: list backends, run a Bell pair, say where.

Authentication is not a token: `qi login` writes ~/.quantuminspire/config.json.
Prefers a real QPU and degrades to an emulator, naming which one ran, because
the free hardware is frequently offline and a chapter must record that fact.
"""

from qiskit import QuantumCircuit, transpile
from qiskit_quantuminspire.qi_provider import QIProvider

HARDWARE = ("Tuna-17", "Tuna-9", "Tuna-5")
EMULATORS = ("QX emulator", "Ry emulator")

provider = QIProvider()
backends = {b.name: b for b in provider.backends()}
for name, b in backends.items():
    print(f"  {name:14s} {b.num_qubits:3d} qubits  {b.status.name}", flush=True)

idle = [n for n, b in backends.items() if b.status.name == "IDLE"]
target = next((n for n in HARDWARE if n in idle), None)
kind = "hardware"
if target is None:
    target = next((n for n in EMULATORS if n in idle), None)
    kind = "emulator"
if target is None:
    raise SystemExit(f"nothing idle; available: {[(n, b.status.name) for n, b in backends.items()]}")

backend = backends[target]
print(f"chosen: {target} ({kind})", flush=True)

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

isa = transpile(qc, backend=backend, optimization_level=1)
print(f"depth after transpile: {isa.depth()}", flush=True)

job = backend.run(isa, shots=1024)
print(f"job id: {job.job_id()}", flush=True)

counts = job.result().get_counts()
total = sum(counts.values())
print(f"counts: {dict(sorted(counts.items()))}", flush=True)
for state in ("00", "11"):
    print(f"  P({state}) = {counts.get(state, 0) / total:.3f}", flush=True)
