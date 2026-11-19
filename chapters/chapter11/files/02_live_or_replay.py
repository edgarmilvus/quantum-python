"""Demo 02: the same code, live or replayed.

Run: python3 chapters/chapter11/files/02_live_or_replay.py

With IONQ_API_KEY set and QUANTUM_LIVE=1 the script submits to IonQ's simulator, which is
free. Otherwise it replays a recorded run. The function that consumes the result does not
know which happened.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import providers as p


def bell_frequencies(backend: p.Backend, shots: int = 512) -> dict:
    """The one function the chapter cares about: run a Bell pair, read both peaks."""
    circuit = p.Circuit(2).add("h", 0).add("cx", 0, 1)
    job = backend.submit(circuit, shots)
    result = backend.result(job)
    return {label: result.frequency(label) for label in sorted(result.counts)}


live = os.getenv("QUANTUM_LIVE", "0") == "1" and bool(os.getenv("IONQ_API_KEY"))

if live:
    backend = p.make("ionq", target="simulator")
    source = "live, IonQ simulator"
else:
    backend = p.Replay("chapter18/0001-bell-1024-ibm")
    source = "replay, run 0001 from ibm_fez"

print(f"source: {source}")
print(f"frequencies: { {k: round(v, 4) for k, v in bell_frequencies(backend).items()} }")
print()
print("the call above is identical in both branches; only the backend object differs")
print("the live simulator gives two outcomes and nothing else; the recorded device")
print("gives four, because readout flips bits on the way out")
print("that is the whole point of the interface: the loop does not branch on provider")
