"""Exercise 1 (repair): the energy computed from one tally.

The Hamiltonian has five terms, three of them diagonal. A program that measures only the Z
basis gets the three and loses the fourth: the energy comes out 19.8 mHa above
Hartree-Fock, which is worse than not doing VQE at all.

Run: python3 chapters/chapter10/files/exercises/ex1_one_basis.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import h2
import vqe


def energy_z_only(z_counts: Dict[str, int]) -> float:
    """The defect: the three diagonal terms, and nothing for the exchange."""
    z_part = sum(h2.TERMS[label] * vqe.average(z_counts, label) for label in ("II", "IZ", "ZI", "ZZ"))
    return z_part + h2.NUCLEAR


def checks(check: Callable[[bool, str], None]) -> None:
    theta = -0.2235
    z = vqe.tally(theta, "Z", 20_000, seed=3)
    x = vqe.tally(theta, "X", 20_000, seed=4)

    defect = energy_z_only(z)
    full = vqe.energy_from_tallies(z, x)["energy"]
    hartree_fock = h2.energy(0.0)
    exact = h2.exact_ground()

    check(defect > hartree_fock, "one basis gives an energy above Hartree-Fock")
    check(abs((defect - hartree_fock) * 1000 - 19.6) < 1.0, "by about 19.6 mHa")
    check(full < hartree_fock, "both tallies give an energy below it")
    check(abs((full - exact) * 1000) < 5.0, "and within five mHa of exact")
    check((defect - exact) * 1000 > 35, "the defect is more than thirty-five mHa above exact")

    check(abs(vqe.average(z, "ZZ")) <= 1.0, "a Z tally can be asked about XX and gives nonsense")
    check(abs(h2.TERMS["XX"]) > 0.1, "and the XX coefficient is not small")

    try:
        vqe.average({}, "IZ")
    except ValueError:
        check(True, "an empty tally is refused")
    else:
        check(False, "an empty tally is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
