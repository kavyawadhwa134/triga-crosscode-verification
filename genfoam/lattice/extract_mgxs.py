"""Extract 2-group MGXS from statepoint to a plain HDF5 (no OpenMC needed
to read the output). Run in genfoam/lattice/ after triga_pin.py:

    conda run -n openmc python extract_mgxs.py

Reads: statepoint.<batches>.h5 + mgxs/mgxs_2g.h5.pkl (Library object).
Writes: mgxs_2g_data.h5 with datasets (OpenMC units: cm-based):
  total[G], absorption[G], fission[G], nu_fission[G], kappa_fission[G],
  scatter[G_in, G_out], chi[G], inv_velocity[G] (s/cm), diffcoef[G] (cm),
  group_edges_eV[G+1] (increasing), keff, keff_std.
Group index 0 = fast.
"""
import glob
import pickle
import h5py
import openmc

with open('mgxs/mgxs_2g.h5.pkl', 'rb') as f:
    lib = pickle.load(f)

sp_file = sorted(glob.glob('statepoint.*.h5'))[-1]
sp = openmc.StatePoint(sp_file)
lib.load_from_statepoint(sp)
u = lib.domains[0]

out = h5py.File('mgxs_2g_data.h5', 'w')
for t, name in [('total', 'total'), ('absorption', 'absorption'),
                ('fission', 'fission'), ('nu-fission', 'nu_fission'),
                ('kappa-fission', 'kappa_fission'), ('chi', 'chi'),
                ('inverse-velocity', 'inv_velocity'),
                ('diffusion-coefficient', 'diffcoef')]:
    out.create_dataset(name, data=lib.get_mgxs(u, t).get_xs().flatten())
out.create_dataset('scatter',
                   data=lib.get_mgxs(u, 'scatter matrix').get_xs())
out.create_dataset('group_edges_eV',
                   data=lib.energy_groups.group_edges)
out.attrs['keff'] = sp.keff.nominal_value
out.attrs['keff_std'] = sp.keff.std_dev
out.attrs['statepoint'] = sp_file
out.attrs['note'] = ('2-group TRIGA pin-cell homogenized MGXS, OpenMC units '
                     '(macroscopic XS in 1/cm, D in cm, IV in s/cm, '
                     'kappa-fission in eV/cm). Group 0 = fast.')
out.close()
print('keff =', sp.keff)
print('Wrote mgxs_2g_data.h5')
