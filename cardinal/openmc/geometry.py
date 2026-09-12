"""pcM independent geometry definitions.

Dimensions from spec/geometry.md (approved problem definition).
"""

import openmc

import materials as mat

# Model 1 - unit cell (approved spec)
FUEL_OR = 1.815  # cm
CLAD_OR = 1.866  # cm
PITCH = 4.235  # cm

# Model 2 - core. PROVISIONAL interpretation, see spec/geometry.md Q1:
# 0.495 m read as DIAMETER, 0.60 m as height.
CORE_DIAMETER = 49.5  # cm
CORE_HEIGHT = 60.0  # cm

# Axial half-thickness of the 2-D slab. Reflective z-planes make this
# neutronically identical to an axially infinite cell (zero axial leakage)
# while giving finite, well-defined cell volumes for tally normalization.
CELL_HALF_Z = 0.5  # cm


def unit_cell(temperature=mat.REF_TEMPERATURE):
    """2-D square-pitch unit cell, fully reflective. k-infinity model.

    No fuel/clad gap (G1) and no Zr central rod (G2): the spec gives exactly
    two radii and a solid fuel meat.
    """
    fuel, clad, water, mats = mat.unit_cell_materials(temperature)

    fuel_surf = openmc.ZCylinder(r=FUEL_OR)
    clad_surf = openmc.ZCylinder(r=CLAD_OR)
    box = openmc.model.RectangularPrism(
        width=PITCH, height=PITCH, boundary_type="reflective"
    )
    zmin = openmc.ZPlane(z0=-CELL_HALF_Z, boundary_type="reflective")
    zmax = openmc.ZPlane(z0=+CELL_HALF_Z, boundary_type="reflective")
    slab = +zmin & -zmax

    fuel_cell = openmc.Cell(name="fuel", fill=fuel, region=-fuel_surf & slab)
    clad_cell = openmc.Cell(
        name="clad", fill=clad, region=+fuel_surf & -clad_surf & slab
    )
    water_cell = openmc.Cell(
        name="water", fill=water, region=+clad_surf & -box & slab
    )

    universe = openmc.Universe(cells=[fuel_cell, clad_cell, water_cell])
    geom = openmc.Geometry(universe)

    cells = {"fuel": fuel_cell, "clad": clad_cell, "water": water_cell}
    return geom, mats, cells


def lattice_core(temperature=mat.REF_TEMPERATURE):
    """Bare heterogeneous core: square lattice of the specified pin, vacuum BCs.

    pcM's PRIMARY core model. Unlike the smeared zone, every material keeps its
    own thermal-scattering kernel, so hydride-bound and water-bound hydrogen
    are both treated correctly. Uses only specified data: the pin radii, the
    4.235 cm pitch, and the core envelope.
    """
    fuel, clad, water, mats = mat.unit_cell_materials(temperature)

    fuel_surf = openmc.ZCylinder(r=FUEL_OR)
    clad_surf = openmc.ZCylinder(r=CLAD_OR)

    pin_fuel = openmc.Cell(name="fuel", fill=fuel, region=-fuel_surf)
    pin_clad = openmc.Cell(name="clad", fill=clad, region=+fuel_surf & -clad_surf)
    pin_water = openmc.Cell(name="pin_water", fill=water, region=+clad_surf)
    pin = openmc.Universe(cells=[pin_fuel, pin_clad, pin_water])

    moderator = openmc.Universe(
        cells=[openmc.Cell(name="outer_water", fill=water)]
    )

    radius = CORE_DIAMETER / 2.0
    n = int(CORE_DIAMETER // PITCH) + 1  # smallest lattice covering the core
    lattice = openmc.RectLattice(name="core lattice")
    lattice.pitch = (PITCH, PITCH)
    lattice.lower_left = (-n * PITCH / 2.0, -n * PITCH / 2.0)
    lattice.universes = [[pin] * n for _ in range(n)]
    lattice.outer = moderator

    radial = openmc.ZCylinder(r=radius, boundary_type="vacuum")
    bottom = openmc.ZPlane(z0=-CORE_HEIGHT / 2.0, boundary_type="vacuum")
    top = openmc.ZPlane(z0=+CORE_HEIGHT / 2.0, boundary_type="vacuum")

    core_cell = openmc.Cell(
        name="core", fill=lattice, region=-radial & +bottom & -top
    )
    geom = openmc.Geometry(openmc.Universe(cells=[core_cell]))
    return geom, mats, {"core": core_cell, "pin_fuel": pin_fuel}, n


def homogenized_core(temperature=mat.REF_TEMPERATURE, sab="zrh"):
    """Bare homogenized cylindrical core, vacuum boundaries. k-effective model.

    G6: bare by specification - no graphite reflector. This is a large
    departure from the physical TRIGA Mark I and is reported as such.

    Carries the single-kernel hydrogen limitation described in
    materials.homogenized_core; `sab` selects which bound is being evaluated.
    """
    core_mat = mat.homogenized_core(temperature, sab=sab)
    mats = openmc.Materials([core_mat])

    radial = openmc.ZCylinder(r=CORE_DIAMETER / 2.0, boundary_type="vacuum")
    bottom = openmc.ZPlane(z0=-CORE_HEIGHT / 2.0, boundary_type="vacuum")
    top = openmc.ZPlane(z0=+CORE_HEIGHT / 2.0, boundary_type="vacuum")

    core_cell = openmc.Cell(
        name="core", fill=core_mat, region=-radial & +bottom & -top
    )

    geom = openmc.Geometry(openmc.Universe(cells=[core_cell]))
    return geom, mats, {"core": core_cell}
