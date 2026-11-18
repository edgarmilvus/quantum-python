"""IBM Quantum through Qiskit Runtime, translated at the boundary.

Everything Qiskit-specific lives here: the circuit object, the primitive, the result
shapes. The chapter's own types never cross into this file's public surface.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

from .base import Backend, BackendError, Circuit, Job, Profile, Result


def _to_qiskit(circuit: Circuit):
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(circuit.wires)
    for name, wires, theta in circuit.ops:
        if name in ("cx", "cnot"):
            qc.cx(wires[0], wires[1])
        elif name == "cz":
            qc.cz(wires[0], wires[1])
        elif theta is None:
            getattr(qc, name)(*wires)
        else:
            getattr(qc, name)(theta, *wires)
    qc.measure_all()
    return qc


class IBM(Backend):
    provider = "ibm"

    def __init__(self, backend: Optional[str] = None, token: Optional[str] = None) -> None:
        # Imported here so the module can be imported without Qiskit installed.
        from qiskit_ibm_runtime import QiskitRuntimeService

        token = token or os.getenv("QISKIT_IBM_TOKEN", "")
        if not token:
            raise BackendError("QISKIT_IBM_TOKEN is not set; use Replay or set the key")
        self._service = QiskitRuntimeService(channel="ibm_quantum_platform")
        backends = self._service.backends(operational=True, simulator=False)
        if not backends:
            raise BackendError("IBM has no operational backend for this instance")
        chosen = None
        for candidate in backends:
            if backend is not None and candidate.name == backend:
                chosen = candidate
                break
        if chosen is None:
            chosen = min(backends, key=lambda b: b.status().pending_jobs)
        self._backend = chosen
        self.name = chosen.name

    def profile(self) -> Profile:
        status = self._backend.status()
        target = getattr(self._backend, "target", None)
        basis = tuple(sorted(target.operation_names)) if target is not None else ()
        return Profile(
            provider=self.provider,
            backend=self.name,
            qubits=self._backend.num_qubits,
            basis=basis,
            queue=int(getattr(status, "pending_jobs", 0)),
        )

    def submit(self, circuit: Circuit, shots: int) -> Job:
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        from qiskit_ibm_runtime import SamplerV2 as Sampler

        self.check_shots(shots)
        qc = _to_qiskit(circuit)
        manager = generate_preset_pass_manager(backend=self._backend, optimization_level=1)
        isa = manager.run(qc)
        sampler = Sampler(mode=self._backend)
        primitive_job = sampler.run([isa], shots=shots)
        self._primitive_jobs = getattr(self, "_primitive_jobs", {})
        self._primitive_jobs[str(primitive_job.job_id())] = primitive_job
        return Job(
            provider=self.provider,
            backend=self.name,
            id=str(primitive_job.job_id()),
            shots=shots,
            depth=isa.depth(),
        )

    def status(self, job: Job) -> str:
        primitive = getattr(self, "_primitive_jobs", {}).get(job.id)
        if primitive is None:
            raise BackendError(f"job {job.id} was not submitted by this adapter")
        return str(primitive.status())

    def result(self, job: Job) -> Result:
        primitive = getattr(self, "_primitive_jobs", {}).get(job.id)
        if primitive is None:
            raise BackendError(f"job {job.id} was not submitted by this adapter")
        raw = primitive.result()
        counts = {str(k): int(v) for k, v in raw[0].data.meas.get_counts().items()}
        return Result(job=job, counts=counts)

    def cancel(self, job: Job) -> None:
        primitive = getattr(self, "_primitive_jobs", {}).get(job.id)
        if primitive is None:
            raise BackendError(f"job {job.id} was not submitted by this adapter")
        primitive.cancel()
