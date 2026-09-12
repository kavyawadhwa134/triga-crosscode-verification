"""pcM fuel temperature coefficient of reactivity.

The defining TRIGA characteristic is a large, prompt, negative fuel temperature
coefficient. It arises from hydrogen bound in ZrH: the ~0.14 eV Einstein
oscillator means a hot fuel lattice up-scatters thermal neutrons out of the
fuel and into the moderator, where they are more likely to be captured or to
leak before returning. This is a much stronger effect than U-238 Doppler alone,
and it is what makes a TRIGA inherently safe under a large reactivity
insertion.

Verifying it is how pcM demonstrates it has modelled a TRIGA rather than a
generic pincell: only the fuel temperature is varied, so the measured
coefficient isolates fuel feedback from moderator density feedback.

Usage:  python temperature_coefficient.py [--temps 296 400 500 600 800]
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import openmc

sys.path.insert(0, str(Path(__file__).parent))

import geometry as geo
import materials as mat
import settings as st

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"


def run_one(fuel_T, moderator_T, config, seed, threads):
    fuel, clad, water, mats = mat.unit_cell_materials(
        moderator_T, fuel_temperature=fuel_T
    )

    fuel_surf = openmc.ZCylinder(r=geo.FUEL_OR)
    clad_surf = openmc.ZCylinder(r=geo.CLAD_OR)
    box = openmc.model.RectangularPrism(
        width=geo.PITCH, height=geo.PITCH, boundary_type="reflective"
    )
    zmin = openmc.ZPlane(z0=-geo.CELL_HALF_Z, boundary_type="reflective")
    zmax = openmc.ZPlane(z0=+geo.CELL_HALF_Z, boundary_type="reflective")
    slab = +zmin & -zmax

    cells = [
        openmc.Cell(name="fuel", fill=fuel, region=-fuel_surf & slab),
        openmc.Cell(name="clad", fill=clad,
                    region=+fuel_surf & -clad_surf & slab),
        openmc.Cell(name="water", fill=water,
                    region=+clad_surf & -box & slab),
    ]
    geom = openmc.Geometry(openmc.Universe(cells=cells))
    s = st.unit_cell_settings(config, geo.PITCH, geo.CELL_HALF_Z, seed=seed)
    # Widen the tolerance: c_H_in_ZrH is tabulated from 296 K upward, so a
    # 293 K request must be allowed to bind to the nearest available data.
    s.temperature = {"method": "interpolation", "tolerance": 100.0}

    rundir = ROOT / "run" / f"tempcoeff_T{int(fuel_T)}"
    rundir.mkdir(parents=True, exist_ok=True)
    cwd = Path.cwd()
    os.chdir(rundir)
    try:
        mats.export_to_xml()
        geom.export_to_xml()
        s.export_to_xml()
        os.environ["OMP_NUM_THREADS"] = str(threads)
        t0 = time.time()
        openmc.run(output=False)
        wall = time.time() - t0
        with openmc.StatePoint(f"statepoint.{config['batches']}.h5") as sp:
            k = sp.keff
            return float(k.nominal_value), float(k.std_dev), wall
    finally:
        os.chdir(cwd)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--temps", type=float, nargs="+",
                   default=[296.0, 400.0, 500.0, 600.0, 800.0, 1000.0])
    p.add_argument("--moderator", type=float, default=293.0)
    p.add_argument("--config", choices=["smoke", "baseline", "production"],
                   default="baseline")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--threads", type=int, default=os.cpu_count())
    args = p.parse_args()

    config = {"smoke": st.SMOKE, "baseline": st.BASELINE,
              "production": st.PRODUCTION}[args.config]

    rows = []
    k_ref = None
    print(f"Fuel temperature sweep, moderator fixed at {args.moderator} K\n")
    print(f"{'T_fuel(K)':>10} {'k_inf':>10} {'sigma':>9} {'rho(pcm)':>10} "
          f"{'d_rho(pcm)':>11} {'alpha(pcm/K)':>13}")

    for T in args.temps:
        k, sd, wall = run_one(T, args.moderator, config, args.seed,
                              args.threads)
        rho = (k - 1.0) / k * 1e5  # reactivity in pcm
        if k_ref is None:
            k_ref, T_ref, rho_ref = k, T, rho
            d_rho, alpha = 0.0, float("nan")
        else:
            d_rho = rho - rho_ref
            alpha = d_rho / (T - T_ref)
        rows.append({
            "T_fuel_K": T, "T_moderator_K": args.moderator,
            "k_inf": f"{k:.6f}", "std_dev": f"{sd:.6f}",
            "reactivity_pcm": f"{rho:.1f}",
            "delta_rho_from_ref_pcm": f"{d_rho:.1f}",
            "alpha_avg_pcm_per_K": "" if T == T_ref else f"{alpha:.3f}",
            "wall_clock_s": f"{wall:.1f}",
        })
        a = "     ref" if T == T_ref else f"{alpha:13.3f}"
        print(f"{T:10.0f} {k:10.6f} {sd:9.6f} {rho:10.1f} {d_rho:11.1f} {a}")

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "pcm_fuel_temperature_coefficient.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    total = float(rows[-1]["delta_rho_from_ref_pcm"])
    span = args.temps[-1] - args.temps[0]
    print(f"\nOverall: {total:.0f} pcm over {span:.0f} K "
          f"=> {total / span:.3f} pcm/K average")
    print("A TRIGA must show a strongly NEGATIVE coefficient.")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
