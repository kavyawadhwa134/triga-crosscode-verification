#!/usr/bin/env python3
"""Decompose the Cardinal vs GeN-Foam core eigenvalue difference.

The two core models differ in more than solution method:

  Cardinal : 3-D bare cylinder, diameter 49.5 cm, height 60 cm,
             heterogeneous pin lattice, continuous-energy Monte Carlo.
  GeN-Foam : 2-D bare slab 49.5 cm x 60 cm (one cell thick, 'empty'
             front/back patches, so infinite in the third direction),
             homogenised, 2-group diffusion, zero flux on the boundary.

Using GeN-Foam's own 2-group constants (results/genfoam/validation_step5.csv)
in an analytic 2-group buckling solution, this script separates the
difference into additive reactivity steps:

  1. homogenisation      Cardinal heterogeneous MC -> Cardinal homogenised MC
  2. solution method     Cardinal homogenised MC   -> 2-group diffusion, same cylinder
  3. core geometry       diffusion, cylinder        -> diffusion, 2-D slab
  4. discretisation      analytic slab              -> GeN-Foam numerical slab

Reactivity differences use rho = 1 - 1/k, so the steps add exactly.
Run from the repository root:  python3 results/comparison/keff_decomposition.py
"""

import csv
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

# GeN-Foam 2-group constants, 1/m and m (validation_step5.csv)
SR1, SR2 = 4.77341, 8.49190        # removal (absorption + out-scatter)
NF1, NF2 = 0.379899, 12.5219       # nu-fission
D1, D2 = 0.00749023, 0.00158363    # diffusion coefficients
S12, S21 = 4.22693, 0.023426       # fast->thermal, thermal->fast scatter

RADIUS, HEIGHT, SLAB_WIDTH = 0.2475, 0.60, 0.495  # m

K_CARDINAL_HET = 1.102059     # results/cardinal/openmc_core.csv, seed 21
K_CARDINAL_HOMOG = 1.145259   # results/cardinal/openmc_core_homog.csv, H in H2O
K_GENFOAM = 1.240544          # results/genfoam/validation_step6.csv
K_INF_OPENMC_LATTICE = 1.38810


def k_two_group(b2):
    """Fundamental-mode k for a bare homogeneous core of buckling b2 (1/m^2)."""
    a1 = D1 * b2 + SR1
    a2 = D2 * b2 + SR2
    return (NF1 + NF2 * S12 / a2) / (a1 - S21 * S12 / a2)


def buckling_cylinder(extrap=0.0):
    return (2.405 / (RADIUS + extrap)) ** 2 + (math.pi / (HEIGHT + 2 * extrap)) ** 2


def buckling_slab(extrap=0.0):
    return (math.pi / (SLAB_WIDTH + 2 * extrap)) ** 2 + (math.pi / (HEIGHT + 2 * extrap)) ** 2


def drho(k_from, k_to):
    """Reactivity change in pcm going from k_from to k_to."""
    return (1.0 / k_from - 1.0 / k_to) * 1e5


def main():
    k_inf = k_two_group(0.0)
    k_cyl = k_two_group(buckling_cylinder())
    k_slab = k_two_group(buckling_slab())
    d_ext = 2.13 * D1  # Marshak extrapolation distance, fast group
    k_cyl_ext = k_two_group(buckling_cylinder(d_ext))

    steps = [
        ("homogenisation", "Cardinal heterogeneous MC", K_CARDINAL_HET,
         "Cardinal homogenised MC", K_CARDINAL_HOMOG),
        ("solution_method", "Cardinal homogenised MC", K_CARDINAL_HOMOG,
         "2-group diffusion, cylinder, zero-flux boundary", k_cyl),
        ("core_geometry", "diffusion, 3-D cylinder", k_cyl,
         "diffusion, 2-D slab", k_slab),
        ("discretisation", "analytic slab", k_slab,
         "GeN-Foam numerical slab", K_GENFOAM),
    ]

    print(f"2-group k_inf from GeN-Foam constants : {k_inf:.5f} "
          f"(OpenMC lattice {K_INF_OPENMC_LATTICE:.5f}, "
          f"{drho(K_INF_OPENMC_LATTICE, k_inf):+.0f} pcm)")
    print(f"diffusion, cylinder (zero flux)        : {k_cyl:.5f}")
    print(f"diffusion, cylinder (extrapolated)     : {k_cyl_ext:.5f}")
    print(f"diffusion, 2-D slab (zero flux)        : {k_slab:.5f} "
          f"(GeN-Foam {K_GENFOAM:.6f})\n")

    rows, total = [], 0.0
    for name, a_lab, a, b_lab, b in steps:
        d = drho(a, b)
        total += d
        rows.append({"step": name, "from": a_lab, "k_from": f"{a:.6f}",
                     "to": b_lab, "k_to": f"{b:.6f}", "delta_rho_pcm": f"{d:+.0f}"})
        print(f"{name:16s} {a:.5f} -> {b:.5f}  {d:+7.0f} pcm")
    print(f"{'total':16s} {K_CARDINAL_HET:.5f} -> {K_GENFOAM:.5f}  {total:+7.0f} pcm "
          f"(direct: {drho(K_CARDINAL_HET, K_GENFOAM):+.0f})")
    print(f"\nmethod step with extrapolated boundary instead: "
          f"{drho(K_CARDINAL_HOMOG, k_cyl_ext):+.0f} pcm")

    out = HERE / "keff_decomposition.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out.relative_to(HERE.parent.parent)}")


if __name__ == "__main__":
    main()
