"""pcM post-processing: power distribution and normalization.

Reads a core statepoint, normalizes kappa-fission to the specified 250 kW,
and writes radial/axial power profiles plus peaking factors.
"""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import openmc

sys.path.insert(0, str(Path(__file__).parent))

import geometry as geo

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
POWER_W = 250.0e3  # spec/operating.md
JOULE_PER_EV = 1.602176634e-19


def main():
    p = argparse.ArgumentParser()
    p.add_argument("statepoint", type=Path)
    p.add_argument("--label", default="core")
    args = p.parse_args()

    pin_stats = None
    with openmc.StatePoint(args.statepoint) as sp:
        k = sp.keff
        try:
            pin = sp.get_tally(name="pin_power")
            pin_stats = (pin.mean.ravel().copy(), pin.std_dev.ravel().copy())
        except LookupError:
            pass
        tally = sp.get_tally(name="power_mesh")
        mean = tally.mean.ravel()
        std = tally.std_dev.ravel()
        mesh = tally.find_filter(openmc.MeshFilter).mesh
        nr = len(mesh.r_grid) - 1
        nz = len(mesh.z_grid) - 1
        r_grid = np.array(mesh.r_grid)
        z_grid = np.array(mesh.z_grid)

    # OpenMC orders mesh bins with r varying fastest, then phi, then z, so the
    # flat array reshapes as (nz, nphi, nr). Reshaping as (nr, 1, nz) instead
    # silently transposes radius and height and yields a spuriously asymmetric
    # axial profile. Transpose back to [r, z].
    heat = mean.reshape(nz, 1, nr)[:, 0, :].T  # eV/source-particle
    heat_std = std.reshape(nz, 1, nr)[:, 0, :].T

    # Cell volumes: annular rings x axial slices
    ring_area = np.pi * (r_grid[1:] ** 2 - r_grid[:-1] ** 2)  # cm^2
    dz = np.diff(z_grid)  # cm
    volume = ring_area[:, None] * dz[None, :]  # cm^3

    total = heat.sum()
    if total <= 0:
        raise SystemExit("no kappa-fission scored - check the mesh covers the core")

    # Normalize to 250 kW
    scale = POWER_W / (total * JOULE_PER_EV)  # source particles per second
    power_w = heat * JOULE_PER_EV * scale  # W per mesh cell
    density = power_w / volume  # W/cm^3

    # Volume-weighted average over fuelled cells. A plain mean over mesh cells
    # would over-weight the small inner rings of a cylindrical mesh.
    fuelled = density > 0
    peak = density[fuelled].max()
    avg = power_w[fuelled].sum() / volume[fuelled].sum()

    radial = power_w.sum(axis=1)
    axial = power_w.sum(axis=0)

    # Physics check: the core is axially symmetric about z=0, so the axial
    # profile must mirror. A large asymmetry means the mesh data is mis-shaped
    # or the source has not converged.
    axial_asymmetry = np.abs(axial - axial[::-1]).max() / axial.max()

    RESULTS.mkdir(exist_ok=True)

    summary = {
        "label": args.label,
        "statepoint": args.statepoint.name,
        "k_eff": f"{k.nominal_value:.6f}",
        "k_eff_std": f"{k.std_dev:.6f}",
        "total_power_W": f"{POWER_W:.1f}",
        "mesh_nr": nr,
        "mesh_nz": nz,
        "peak_power_density_W_cm3": f"{peak:.4f}",
        "avg_power_density_W_cm3": f"{avg:.4f}",
        "mesh_peak_to_average": f"{peak / avg:.4f}",
        "max_rel_unc_in_peak_cell": f"{(heat_std / np.maximum(heat, 1e-30)).max():.4f}",
        "axial_symmetry_residual": f"{axial_asymmetry:.4f}",
    }

    if pin_stats is not None:
        pin_mean, pin_std = pin_stats
        live = pin_mean > 0
        n_pins = int(live.sum())
        pin_power = pin_mean[live] * JOULE_PER_EV * scale  # W per pin
        pin_avg = pin_power.mean()
        hottest = int(np.argmax(pin_power))
        summary.update({
            "n_fuelled_pins": n_pins,
            "pin_peak_power_W": f"{pin_power.max():.2f}",
            "pin_avg_power_W": f"{pin_avg:.2f}",
            "pin_peak_to_average": f"{pin_power.max() / pin_avg:.4f}",
            "pin_min_to_average": f"{pin_power.min() / pin_avg:.4f}",
            "pin_power_sum_W": f"{pin_power.sum():.1f}",
            "hottest_pin_rel_unc": f"{pin_std[live][hottest] / pin_mean[live][hottest]:.5f}",
        })

        with open(RESULTS / f"pcm_pin_power_{args.label}.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["pin_index", "power_W", "normalized_to_average"])
            for i, val in enumerate(pin_power):
                w.writerow([i, f"{val:.3f}", f"{val / pin_avg:.5f}"])
    with open(RESULTS / f"pcm_power_summary_{args.label}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary))
        w.writeheader()
        w.writerow(summary)

    with open(RESULTS / f"pcm_power_radial_{args.label}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["r_inner_cm", "r_outer_cm", "power_W", "power_fraction"])
        for i in range(nr):
            w.writerow([f"{r_grid[i]:.4f}", f"{r_grid[i + 1]:.4f}",
                        f"{radial[i]:.2f}", f"{radial[i] / radial.sum():.6f}"])

    with open(RESULTS / f"pcm_power_axial_{args.label}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["z_lower_cm", "z_upper_cm", "power_W", "power_fraction"])
        for j in range(nz):
            w.writerow([f"{z_grid[j]:.4f}", f"{z_grid[j + 1]:.4f}",
                        f"{axial[j]:.2f}", f"{axial[j] / axial.sum():.6f}"])

    print(f"k_eff               = {k.nominal_value:.6f} +/- {k.std_dev:.6f}")
    print(f"peak power density  = {peak:.4f} W/cm^3")
    print(f"avg  power density  = {avg:.4f} W/cm^3")
    print(f"mesh peak/average   = {peak / avg:.4f}  (mesh-resolution dependent)")
    if pin_stats is not None:
        print(f"fuelled pins        = {summary['n_fuelled_pins']}")
        print(f"pin peak/average    = {summary['pin_peak_to_average']}  (mesh-independent)")
        print(f"pin power sum       = {summary['pin_power_sum_W']} W  (should be 250000)")
    print(f"axial symmetry res. = {axial_asymmetry:.4f}  (0 = perfectly symmetric)")
    print(f"wrote results/pcm_power_*_{args.label}.csv")


if __name__ == "__main__":
    main()
