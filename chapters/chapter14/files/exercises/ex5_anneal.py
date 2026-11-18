"""Exercise 5, file 3 of 3: the wiring.

Runs the exact sampler, the annealer and the embedded problem, then asks the pure
file for a summary and the renderer for text. This is the only file that builds a
sampler and the only one that prints.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from anneal import embed, instances, sampler

from plan_core import reads_for_summary, summarise, verdict
from plan_render import render


def direct(reads: int = 200, sweeps: int = 300) -> Dict[str, float]:
    """The twelve-variable instance, sampled directly."""
    coupling = instances.spin_glass()
    optimum = sampler.Exact({}, coupling).sample().best()[0]
    result = sampler.Annealer({}, coupling, 0.0, sweeps=sweeps, seed=11).sample(reads)
    return summarise(result, optimum)


def embedded(reads: int = 50, sweeps: int = 300, strength: float = 1.0) -> Dict[str, float]:
    """The five-variable instance, through a Chimera embedding and back."""
    graph = embed.Chimera(2, 2)
    linear, coupling, embedding = embed.five_variable_instance()
    optimum = sampler.Exact(linear, coupling).sample().best()[0]
    physical_linear, physical_coupling = embed.physical_problem(
        linear, coupling, embedding, strength, graph
    )
    physical = sampler.Annealer(physical_linear, physical_coupling, 0.0, sweeps=sweeps, seed=5).sample(reads)
    logical_samples = [embed.unembed(sample, embedding)[0] for sample in physical.samples]
    energies = [
        sampler.ising_energy(linear, coupling, 0.0, logical) for logical in logical_samples
    ]
    result = sampler.Result(
        samples=logical_samples,
        energies=energies,
        occurrences=list(physical.occurrences),
    )
    return summarise(result, optimum)


def report(summary: Dict[str, float]) -> str:
    target = reads_for_summary(summary)
    return render(summary, "Annealing on twelve variables", verdict(summary), target)


def checks(check: Callable[[bool, str], None]) -> None:
    summary = direct()
    text = report(summary)

    check("Annealing on twelve variables" in text, "the title names the instance")
    check("verdict" in text, "the table ends on a verdict")
    check("nan" not in text.lower(), "no number failed to compute")

    check(abs(summary["best"] + 24.0) < 1e-9, "the best read is the optimum")
    check(abs(summary["gap"]) < 1e-9, "so the gap is zero")
    check(summary["success"] > 0.95, "and more than 95% of reads reach it")
    check(summary["reads"] == 200, "the report counts two hundred reads")
    check(verdict(summary) == "at the optimum", "the verdict says so")

    near = dict(summary)
    near["success"] = 0.6
    check(verdict(near) == "usually at the optimum", "sixty percent is a different verdict")
    near["success"] = 0.2
    check(verdict(near) == "sometimes at the optimum", "and so is twenty")

    far = dict(summary)
    far["gap"] = 2.0
    check(verdict(far) == "missed the optimum", "a gap overrides the rate")

    check(reads_for_summary(summary) == 1, "a 99% run needs one read for 95%")
    check(reads_for_summary({"success": 0.05}) == 59, "a one-in-twenty run needs fifty-nine")

    through = embedded()
    check(abs(through["best"] + 5.0) < 1e-9, "the embedded run also finds its optimum")
    check(through["reads"] == 50, "over fifty reads")

    check(report(direct()) == text, "the report is deterministic")

    try:
        summarise(sampler.Result(samples=[], energies=[], occurrences=[]), 0.0)
    except ValueError:
        check(True, "an empty result is refused")
    else:
        check(False, "an empty result is refused")

    try:
        reads_for_summary({"success": 0.0})
    except ValueError:
        check(True, "a run that never succeeds has no read count")
    else:
        check(False, "a run that never succeeds has no read count")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
