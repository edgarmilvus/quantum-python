"""The noise package: channels, a device model, a simulator, mitigation.

The surface is deliberately small. `noise.states` holds the linear algebra,
`noise.channels` the three Kraus sets, `noise.device` what the hardware says
about itself, `noise.confusion` the readout matrix, `noise.simulate` the noisy
circuit, `noise.zne` the folding and extrapolation, and `noise.fit` the two
moves that turn a measurement into a rate and a rate into a prediction.
"""

from . import channels, confusion, device, fit, simulate, states, zne
from .device import Budget, Rates, Readout, calibration_budget, readout_from_record, sigma_binomial
from .simulate import Simulator, bell, chsh_setting
from .zne import Fit, Point, exponential, fold, linear

__all__ = [
    "Budget",
    "Fit",
    "Point",
    "Rates",
    "Readout",
    "Simulator",
    "bell",
    "calibration_budget",
    "channels",
    "chsh_setting",
    "confusion",
    "device",
    "exponential",
    "fit",
    "fold",
    "linear",
    "readout_from_record",
    "sigma_binomial",
    "simulate",
    "states",
    "zne",
]
