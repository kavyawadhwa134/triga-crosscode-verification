"""pcM 3-D pincell OpenMC model for Cardinal coupling.

Same specified materials and radii as the 2-D k-infinity model, extended
axially so temperature and power can vary along the pin.

Axial layers are explicit cells at the root universe level, which is what
Cardinal's OpenMCCellAverageProblem maps onto the MOOSE mesh (cell_level = 0).

Usage:  python make_coupled_model.py [-n 20]
"""

import sys
from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import openmc

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "openmc"))

import materials as mat
from geometry import CLAD_OR, FUEL_OR, PITCH

HEIGHT = 60.0  # cm, core height from spec/geometry.md
T_INLET = 293.0  # K, spec/operating.md


def main():
    ap = ArgumentParser()
    ap.add_argument("-n", dest="n_axial", type=int, default=20,
                    help="axial cell divisions (must match the MOOSE mesh)")
    ap.add_argument("--particles", type=int, default=5000)
    ap.add_argument("--batches", type=int, default=100)
    ap.add_argument("--inactive", type=int, default=25)
    args = ap.parse_args()

    fuel, clad, water, materials = mat.unit_cell_materials(T_INLET)
    materials.export_to_xml()

    fuel_surf = openmc.ZCylinder(r=FUEL_OR)
    clad_surf = openmc.ZCylinder(r=CLAD_OR)
    box = openmc.model.RectangularPrism(
        width=PITCH, height=PITCH, axis="z", origin=(0.0, 0.0),
        boundary_type="reflective",
    )

    # Radially reflective (interior pin of an infinite lattice), axially vacuum
    # so the axial power shape is physical for the thermal-fluid problem.
    z_coords = np.linspace(0.0, HEIGHT, args.n_axial + 1)
    planes = [openmc.ZPlane(z0=z) for z in z_coords]
    planes[0].boundary_type = "vacuum"
    planes[-1].boundary_type = "vacuum"

    cells = []
    for i in range(args.n_axial):
        layer = +planes[i] & -planes[i + 1]
        cells.append(openmc.Cell(fill=fuel, region=-fuel_surf & layer,
                                 name=f"fuel{i}"))
        cells.append(openmc.Cell(fill=clad,
                                 region=+fuel_surf & -clad_surf & layer,
                                 name=f"clad{i}"))
        cells.append(openmc.Cell(fill=water,
                                 region=+clad_surf & -box & layer,
                                 name=f"water{i}"))

    openmc.Geometry(openmc.Universe(name="root", cells=cells)).export_to_xml()

    settings = openmc.Settings()
    settings.particles = args.particles
    settings.batches = args.batches
    settings.inactive = args.inactive
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box((-PITCH / 2, -PITCH / 2, 0.0),
                               (PITCH / 2, PITCH / 2, HEIGHT)),
        constraints={"fissionable": True},
    )
    # Windowed multipole is not available for every nuclide in this library, so
    # interpolation between the library's temperature grid points is used.
    settings.temperature = {
        "default": T_INLET,
        "method": "interpolation",
        "range": (250.0, 3000.0),
    }
    settings.export_to_xml()

    print(f"wrote 3-D pincell: {args.n_axial} axial layers, "
          f"{len(cells)} cells, height {HEIGHT} cm")


if __name__ == "__main__":
    main()
