"""Demo 05: the same 36 points, on the simulator and on ibm_marrakesh.

Run: python3 chapters/chapter13/files/05_hardware.py

Reads runs/chapter13/0022-qaoa-maxcut4-36x1024-ibm/result.json, one job of 36 circuits at 1,024 shots
each. The question is not whether the device found the optimum; it is whether the
surface it returned has the same shape as the simulated one. It does, to four
decimals of correlation, and it is flatter.
"""

import json
from pathlib import Path

import numpy as np

from qaoa import graph as g, qaoa

ROOT = Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/chapter13/0022-qaoa-maxcut4-36x1024-ibm/result.json").read_text())
instance = g.Graph(n=record["graph"]["n"], edges=tuple(tuple(edge) for edge in record["graph"]["edges"]))
optimum, _ = instance.max_cut()

rows = []
for entry in record["results"]:
    counts = {int(key, 2): value for key, value in entry["counts"].items()}
    measured = qaoa.expected_cut_from_counts(instance, counts)
    sigma = qaoa.cut_sigma(instance, counts)
    simulated = qaoa.expected_cut(instance, qaoa.state_for(instance, [entry["beta"]], [entry["gamma"]]))
    rows.append(
        {
            "beta": entry["beta"],
            "gamma": entry["gamma"],
            "simulated": simulated,
            "measured": measured,
            "sigma": sigma,
        }
    )

simulated_values = np.array([row["simulated"] for row in rows])
measured_values = np.array([row["measured"] for row in rows])
mean_sigma = float(np.mean([row["sigma"] for row in rows]))

print(f"job {record['job_id']} on {record['backend']}, {len(rows)} circuits, "
      f"{record['shots']} shots, depth {record['transpiled_depth']}")
print()
print(f"{'beta':>7s}{'gamma':>8s}{'simulated':>11s}{'measured':>10s}{'gap':>9s}{'sigma':>8s}")
for row in rows[:6]:
    print(f"{row['beta']:7.4f}{row['gamma']:8.4f}{row['simulated']:11.4f}{row['measured']:10.4f}"
          f"{row['measured'] - row['simulated']:+9.4f}{row['sigma']:8.4f}")
print(f"... {len(rows) - 6} more rows, all in the record")
print()

correlation = float(np.corrcoef(simulated_values, measured_values)[0, 1])
rmse = float(np.sqrt(np.mean((measured_values - simulated_values) ** 2)))
print(f"correlation between the two surfaces: {correlation:.4f}")
print(f"root mean square gap: {rmse:.4f}, against a shot error of {mean_sigma:.4f} a point")
print()

best_simulated = int(np.argmax(simulated_values))
best_measured = int(np.argmax(measured_values))
same = best_simulated == best_measured
print(f"best simulated point: beta {rows[best_simulated]['beta']:.4f}, gamma {rows[best_simulated]['gamma']:.4f}, "
      f"{rows[best_simulated]['simulated']:.4f}")
print(f"best measured point:  beta {rows[best_measured]['beta']:.4f}, gamma {rows[best_measured]['gamma']:.4f}, "
      f"{rows[best_measured]['measured']:.4f}")
print(f"same grid point: {same}")
print()

slope, intercept = np.polyfit(simulated_values, measured_values, 1)
print(f"a line through the two surfaces has slope {slope:.4f} and intercept {intercept:.4f}")
print(f"a slope below one is the device compressing the landscape: the peaks come down")
print(f"and the troughs come up. The measured range is [{measured_values.min():.3f}, "
      f"{measured_values.max():.3f}]")
print(f"against a simulated [{simulated_values.min():.3f}, {simulated_values.max():.3f}].")
print()
print(f"mean over the grid: simulated {simulated_values.mean():.4f}, measured {measured_values.mean():.4f}")
print(f"the noise is close to unbiased on average and still costs the peak "
      f"{rows[best_simulated]['simulated'] - rows[best_measured]['measured']:.4f} of cut.")
print()
print(f"approximation ratio at the best measured point: "
      f"{qaoa.approximation_ratio(rows[best_measured]['measured'], optimum):.4f}")
print(f"the same point on the simulator: "
      f"{qaoa.approximation_ratio(rows[best_measured]['simulated'], optimum):.4f}")
