"""Demo 03: what the providers disagree about, read from their profiles.

Run: python3 chapters/chapter11/files/03_capabilities.py

The interface hides the API shape, not the physics. A reader still has to choose a
provider, and the differences are qubit count, basis, queue and price.
"""

import providers as p

CASES = {
    "ibm_fez (recorded)": "chapter18/0001-bell-1024-ibm",
    "ibm_marrakesh (recorded)": "chapter06/0011-bv-101-1024-ibm",
    "IonQ simulator (recorded)": "chapter18/0003-bell-1024-ionq",
    "Quantum Inspire emulator (recorded)": "chapter18/0002-bell-1024-qi",
}

print(f"{'source':34s}{'qubits':>8s}{'queue':>7s}{'basis':>8s}")
for label, case in CASES.items():
    backend = p.Replay(case)
    profile = backend.profile()
    print(f"{label:34s}{profile.qubits:8d}{profile.queue:7d}{len(profile.basis):8d}")

print()
print("prices, per task and per shot, in USD:")
print(f"{'provider':18s}{'per task':>10s}{'per shot':>10s}   note")
for name, price in p.PRICES.items():
    print(f"{name:18s}{price.per_task:10.3f}{price.per_shot:10.4f}   {price.note}")

print()
print("a 1024-shot job, quoted:")
for name in ("replay", "ibm", "ionq-simulator", "ionq", "braket-qpu"):
    print(f"  {name:18s}{p.PRICES[name].quote(1024):8.2f} USD")
