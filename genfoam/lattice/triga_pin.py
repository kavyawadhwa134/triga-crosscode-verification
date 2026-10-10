"""TRIGA Mark I pin-cell (infinite lattice) — Step 5.

Fuel: standard TRIGA 8.5 wt% U @ 20% U235 in ZrH1.65, SS304 clad.
  Sources: NRC tech specs (R-38/ML12031A170: 8.5 wt% U, <20% U235,
  H/Zr nominal 1.65, 304SS clad nominal 0.020 in = 0.0508 cm);
  UT TRIGA overview (105-type dims): fuel meat OD 36.3 mm.
Geometry: square pin cell of pitch P_SQ preserving the reference
  hexagonal cell area: (sqrt(3)/2)*4.55^2 = 17.93 cm^2 -> P_SQ = 4.235 cm,
  reflective boundaries (exact infinite square lattice; second-order
  difference vs hexagonal at equal cell area).
  2-D (infinite in z); axial reflectors/poisons are full-core detail.
Materials data: ENDF/B-VIII.0 official HDF5 (OPENMC_CROSS_SECTIONS).
Produces: materials/geometry/settings/tallies XML, k-inf run,
  2-group MGXS (0.625 eV cutoff) homogenized over the pin cell
  -> mgxs_2g.h5
"""
import subprocess
import glob
import openmc
import openmc.mgxs

PITCH = 4.235           # cm, square pitch, area-equivalent to hex p=4.55
R_FUEL = 1.815          # cm, fuel meat radius (36.3 mm OD)
R_CLAD = 1.866          # cm, clad outer radius (+0.051 cm SS304)
GROUPS = [0.0, 0.625, 20.0e6]   # eV, increasing; groups: [0,0.625]=thermal, [0.625,20M]=fast

# ---------------------------------------------------------------- materials
fuel = openmc.Material(name='uzrh_fuel')
fuel.set_density('g/cc', 6.0)          # ~theoretical for 8.5 wt% U-ZrH1.65
fuel.add_nuclide('U235', 1.7, 'wo')    # 8.5 wt% U x 20 % enrichment
fuel.add_nuclide('U238', 6.8, 'wo')
fuel.add_element('Zr', 89.862, 'wo')   # 91.5 wt% ZrH1.65 -> Zr fraction
fuel.add_nuclide('H1', 1.638, 'wo')    # 91.5 wt% ZrH1.65 -> H fraction
fuel.add_s_alpha_beta('c_H_in_ZrH')
fuel.add_s_alpha_beta('c_Zr_in_ZrH')

clad = openmc.Material(name='ss304')
clad.set_density('g/cc', 7.9)
clad.add_element('Fe', 70.5, 'wo')
clad.add_element('Cr', 19.0, 'wo')
clad.add_element('Ni', 9.0, 'wo')
clad.add_element('Mn', 1.0, 'wo')
clad.add_element('Si', 0.5, 'wo')

water = openmc.Material(name='water')
water.set_density('g/cc', 1.0)
water.add_nuclide('H1', 2.0, 'ao')
water.add_nuclide('O16', 1.0, 'ao')
water.add_s_alpha_beta('c_H_in_H2O')

materials = openmc.Materials([fuel, clad, water])

# ---------------------------------------------------------------- geometry
fuel_cyl = openmc.ZCylinder(r=R_FUEL)
clad_cyl = openmc.ZCylinder(r=R_CLAD)
fuel_cell = openmc.Cell(name='fuel', fill=fuel, region=-fuel_cyl)
clad_cell = openmc.Cell(name='clad', fill=clad,
                        region=+fuel_cyl & -clad_cyl)
mod_cell = openmc.Cell(name='water', fill=water, region=+clad_cyl)
pin_univ = openmc.Universe(name='pin', cells=[fuel_cell, clad_cell, mod_cell])

lat = openmc.RectLattice(name='core_lat')
lat.pitch = (PITCH, PITCH)
lat.lower_left = (-PITCH / 2, -PITCH / 2)
lat.universes = [[pin_univ]]

xmin = openmc.XPlane(-PITCH / 2, boundary_type='reflective')
xmax = openmc.XPlane(PITCH / 2, boundary_type='reflective')
ymin = openmc.YPlane(-PITCH / 2, boundary_type='reflective')
ymax = openmc.YPlane(PITCH / 2, boundary_type='reflective')
root_cell = openmc.Cell(name='root', fill=lat,
                        region=+xmin & -xmax & +ymin & -ymax)
geometry = openmc.Geometry(openmc.Universe(name='root', cells=[root_cell]))

# ---------------------------------------------------------------- settings
settings = openmc.Settings()
settings.run_mode = 'eigenvalue'
settings.batches = 70
settings.inactive = 20
settings.particles = 8000
settings.source = openmc.IndependentSource(
    space=openmc.stats.Box(*[[-PITCH / 2] * 3, [PITCH / 2] * 3]))

# ---------------------------------------------------------------- MGXS library
groups = openmc.mgxs.EnergyGroups(GROUPS)
lib = openmc.mgxs.Library(geometry)
lib.energy_groups = groups
lib.mgxs_types = ['total', 'absorption', 'fission', 'nu-fission',
                  'kappa-fission', 'scatter matrix',
                  'chi', 'inverse-velocity', 'diffusion-coefficient']
lib.domain_type = 'universe'
lib.domains = [geometry.root_universe]
lib.build_library()

tallies = openmc.Tallies()
lib.add_to_tallies_file(tallies, merge=True)

materials.export_to_xml()
geometry.export_to_xml()
settings.export_to_xml()
tallies.export_to_xml()

print('Running OpenMC (k-inf + 2-group tallies) ...', flush=True)
import sys
if '--no-run' not in sys.argv:
    subprocess.run(['openmc'], check=True)

sp_file = sorted(glob.glob('statepoint.*.h5'))[-1]
print('Loading', sp_file, flush=True)
sp = openmc.StatePoint(sp_file)
lib.load_from_statepoint(sp)
lib.dump_to_file('mgxs_2g.h5')

# ---------------------------------------------------------------- summary
tot = lib.get_mgxs(geometry.root_universe, 'total')
abs_xs = lib.get_mgxs(geometry.root_universe, 'absorption')
nuf = lib.get_mgxs(geometry.root_universe, 'nu-fission')
print('k-inf           :', sp.keff)
print('total           :', tot.get_xs().flatten())
print('absorption      :', abs_xs.get_xs().flatten())
print('nu-fission      :', nuf.get_xs().flatten())
print('Wrote mgxs_2g.h5')
