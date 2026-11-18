"""Export the ibm_fez calibration that chapter 12 uses, as a file.

The provider ships a saved calibration of ibm_fez inside qiskit-ibm-runtime as
the fake backend `FakeFez`. This script reads it once, transpiles the chapter's
Grover circuit against it, and writes every gate's error rate to
runs/0020-ibm-fez-calibration/circuit.json. The chapter then reads the file and
does its own arithmetic, offline, with no Qiskit.

Run: python3 tools/export_calibration.py
"""

from __future__ import annotations

import json
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/0020-ibm-fez-calibration"
SEED = 7
MARKED = 5
STEPS = 2


def grover(marked: int = MARKED, n: int = 3, steps: int = STEPS) -> QuantumCircuit:
    """The chapter 7 circuit: H, then steps of (oracle, diffusion), then measure."""
    circuit = QuantumCircuit(n)
    for qubit in range(n):
        circuit.h(qubit)
    for _ in range(steps):
        bits = [(marked >> i) & 1 for i in range(n)]
        for wire, bit in enumerate(bits):
            if bit == 0:
                circuit.x(wire)
        circuit.h(n - 1)
        circuit.ccx(0, 1, n - 1)
        circuit.h(n - 1)
        for wire, bit in enumerate(bits):
            if bit == 0:
                circuit.x(wire)
        for qubit in range(n):
            circuit.h(qubit)
        for qubit in range(n):
            circuit.x(qubit)
        circuit.h(n - 1)
        circuit.ccx(0, 1, n - 1)
        circuit.h(n - 1)
        for qubit in range(n):
            circuit.x(qubit)
        for qubit in range(n):
            circuit.h(qubit)
    circuit.measure_all()
    return circuit


def error_of(target, gate: str, qubits) -> float:
    properties = target[gate][tuple(qubits)]
    value = getattr(properties, "error", 0.0)
    return float(value or 0.0)


def main() -> int:
    backend = FakeFez()
    target = backend.target
    manager = generate_preset_pass_manager(
        backend=backend, optimization_level=1, seed_transpiler=SEED
    )
    isa = manager.run(grover())

    ops = []
    measured = set()
    for instruction in isa.data:
        name = instruction.operation.name
        qubits = [isa.find_bit(qubit).index for qubit in instruction.qubits]
        if name in ("cz", "ecr", "cx"):
            ops.append({"gate": name, "qubits": qubits, "error": error_of(target, name, qubits)})
        elif name in ("sx", "x", "rz", "h"):
            rate = error_of(target, "sx", [qubits[0]]) if name in ("sx", "x") else 0.0
            ops.append({"gate": name, "qubits": qubits, "error": rate})
        elif name == "measure":
            measured.add(qubits[0])

    readout = [
        {"wire": wire, "qubit": qubit, "error": error_of(target, "measure", [qubit])}
        for wire, qubit in enumerate(isa.layout.final_index_layout())
    ]

    edge_errors = sorted(
        float(getattr(properties, "error", 0.0) or 0.0)
        for key, properties in target["cz"].items()
        if len(key) == 2 and key[0] < key[1]
    )

    record = {
        "case": "ibm-fez-grover-calibration",
        "source": "qiskit-ibm-runtime FakeFez, a saved calibration of ibm_fez",
        "exported_with": "qiskit-ibm-runtime fake_provider, optimization_level=1, seed_transpiler=7",
        "circuit": {
            "n": 3,
            "marked": MARKED,
            "marked_bits": format(MARKED, "03b"),
            "steps": STEPS,
            "depth": isa.depth(),
            "two_qubit_gates": sum(1 for op in ops if op["gate"] in ("cz", "ecr", "cx")),
            "single_qubit_gates": sum(1 for op in ops if op["gate"] not in ("cz", "ecr", "cx")),
            "ideal_probability": 0.9453124999999959,
        },
        "ops": ops,
        "readout": readout,
        "cz_catalogue": {
            "edges": len(edge_errors),
            "min": edge_errors[0],
            "median": edge_errors[len(edge_errors) // 2],
            "max": edge_errors[-1],
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "circuit.json").write_text(json.dumps(record, indent=2) + "\n")

    print(f"depth {record['circuit']['depth']}, {record['circuit']['two_qubit_gates']} two-qubit gates")
    print(f"readout qubits {[r['qubit'] for r in readout]}")
    print(f"cz catalogue {record['cz_catalogue']}")
    print(f"wrote {OUT / 'circuit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
