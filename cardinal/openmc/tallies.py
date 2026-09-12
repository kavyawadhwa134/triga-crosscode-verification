"""pcM independent tally definitions.

Two-group structure from spec/operating.md (0.625 eV cutoff).
"""

import openmc

from settings import GROUP_EDGES


def two_group_filter():
    return openmc.EnergyFilter(GROUP_EDGES)


def unit_cell_tallies(cells):
    """Per-region two-group reaction rates for the k-infinity model."""
    energy = two_group_filter()
    tallies = openmc.Tallies()

    for name, cell in cells.items():
        t = openmc.Tally(name=f"{name}_2group")
        t.filters = [openmc.CellFilter(cell), energy]
        t.scores = ["flux", "total", "absorption", "fission", "nu-fission"]
        tallies.append(t)

    # Spectrum-integrated core-wide balance, for the k-from-tallies check
    total = openmc.Tally(name="global_2group")
    total.filters = [energy]
    total.scores = ["flux", "absorption", "fission", "nu-fission"]
    tallies.append(total)

    return tallies


def pin_power_tally(pin_fuel_cell):
    """Power per individual fuel pin, via distribcell.

    Mesh-independent: a cylindrical mesh that is not aligned with the square
    lattice produces spurious peaking, because some cells land on fuel and
    others on water. Per-pin power is the physically meaningful peaking metric.
    """
    t = openmc.Tally(name="pin_power")
    t.filters = [openmc.DistribcellFilter(pin_fuel_cell)]
    t.scores = ["kappa-fission"]
    return t


def core_tallies(cell, radius, height, nr=10, nz=20):
    """Core model: two-group balance plus a power distribution mesh."""
    energy = two_group_filter()
    tallies = openmc.Tallies()

    balance = openmc.Tally(name="core_2group")
    balance.filters = [openmc.CellFilter(cell), energy]
    balance.scores = ["flux", "total", "absorption", "fission", "nu-fission"]
    tallies.append(balance)

    # Cylindrical mesh for radial/axial power shape and peak/average factor
    mesh = openmc.CylindricalMesh(
        r_grid=[radius * i / nr for i in range(nr + 1)],
        z_grid=[-height / 2.0 + height * k / nz for k in range(nz + 1)],
        phi_grid=[0.0, 2.0 * 3.141592653589793],
    )
    power = openmc.Tally(name="power_mesh")
    power.filters = [openmc.MeshFilter(mesh)]
    power.scores = ["kappa-fission"]
    tallies.append(power)

    return tallies, mesh
