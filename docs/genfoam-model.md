# GeN-Foam model: methods and results

The deterministic side of the TRIGA Mark I cross-code study: two-group
diffusion coupled to porous-medium thermal-hydraulics in
[GeN-Foam](https://gitlab.com/foam-for-nuclear/GeN-Foam) (OpenFOAM), with
group constants condensed from an OpenMC lattice calculation. Inputs are in
[`../genfoam/`](../genfoam/); results are in
[`../results/genfoam/`](../results/genfoam/).

## 1. Workflow

```
genfoam/lattice/triga_pin.py         OpenMC pin cell -> k-inf + 2-group MGXS library
genfoam/lattice/extract_mgxs.py      statepoint -> mgxs_2g_data.h5 (plain HDF5)
genfoam/tools/openmc2genfoam.py      HDF5 -> GeN-Foam nuclearData dictionary
genfoam/triga_steady/                eigenvalue + coupled steady state, 0-100 s
genfoam/triga_transient_rod/         +0.5 $ rod-withdrawal transient, 100-106 s
```

## 2. Lattice and group constants

| Item | Value |
|---|---|
| Geometry | 2-D square pin cell, pitch 4.235 cm, reflective |
| Code / data | OpenMC 0.16.0, ENDF/B-VIII.0 with `c_H_in_ZrH`, `c_Zr_in_ZrH`, `c_H_in_H2O` |
| Statistics | 8000 particles × 70 batches (20 inactive) |
| k-infinity | **1.38810 ± 0.00123** |
| Group structure | 2 groups, thermal cutoff 0.625 eV |
| Clad | SS304 at 7.9 g/cm³ (Cardinal used 8.00 g/cm³; see [`specification.md`](specification.md)) |

The converter maps OpenMC MGXS to GeN-Foam diffusion data: removal =
absorption + out-scatter, P0 scattering matrix, ν-fission, κ-fission for power,
diffusion coefficients and inverse velocities converted to SI. Delayed-neutron
data are U-235 Keepin six-group values.

**Consistency check.** Solving the condensed constants analytically for an
infinite medium gives k∞ = 1.38873, within 33 pcm of the OpenMC lattice value.

## 3. Steady state

| Item | Value |
|---|---|
| Core geometry | **2-D slab**, 0.495 m wide × 0.60 m tall, one cell (0.04235 m) thick with `empty` front/back patches |
| Mesh | 20 × 24 cells |
| Neutronics | 2-group eigenvalue diffusion, zero flux on all boundaries |
| Thermal-hydraulics | porous medium (fluid fraction 0.39, D_h = 2.4 cm), laminar, buoyancy on, forced inlet 0.2 m/s at 293 K |
| Fuel | sub-scale pin model (`nuclearFuelPin`): fuel radius 1.815 cm, clad 1.815–1.866 cm, k_fuel = 18 W/m·K |
| Power | 250 kW |

| Result | Value |
|---|---|
| **k-effective** | **1.240544** |
| Maximum coolant temperature | 306.47 K |
| Maximum average fuel temperature | 594.2 K |
| Power peaking (max/avg) | 2.45 (analytic cos × cos slab value π²/4 = 2.47) |

**Solver verification.** The analytic two-group solution for the same slab,
with the same constants and zero-flux boundary, gives k = 1.24030, within
16 pcm of the GeN-Foam result
([`../results/comparison/keff_decomposition.py`](../results/comparison/keff_decomposition.py)).

The slab is a deliberate first-tier simplification. It leaks much less than the
3-D cylinder used by Cardinal, which accounts for about 7000 pcm of the
difference between the two core eigenvalues; see
[`../results/comparison/COMPARISON.md`](../results/comparison/COMPARISON.md).

## 4. Reactivity insertion transient

| Item | Value |
|---|---|
| Kinetics | point kinetics from the steady flux shape; Keepin 6-group, β = 0.0065, Λ = 43 µs |
| Insertion | +0.5 $ (0.00325 Δk/k) ramped over 100.0–100.5 s, then held |
| Feedback | fuel temperature only, constant `feedbackCoeffTFuel` = −1.0 × 10⁻⁴ K⁻¹ (published TRIGA prompt coefficient) |

| Result | Value |
|---|---|
| Peak power | **489.7 kW** at t = 100.56 s |
| New equilibrium | 304.9 kW |
| Average fuel temperature | 511.70 → 544.59 K |
| Net reactivity at 106 s | −3.87 pcm (+325 external, −328.9 feedback) |

Cardinal's computed bare-core coefficient in the 500–600 K band,
−10.79 ± 0.82 pcm/K, agrees with the −10.0 pcm/K input to within one standard
deviation. The computed coefficient varies from −6.3 to −10.8 pcm/K over
296–1000 K, so a temperature-dependent coefficient would be needed for larger
excursions.

## 5. Solver acceptance

Before the TRIGA calculation, GeN-Foam was checked against its reference
cases (`results/genfoam/validation_step2.csv`): the 3-D SmallESFR eigenvalue
agrees with the reference to 4.9 × 10⁻⁵, and four 2-D point-kinetics cases
(steady, transient without and with driveline expansion, boron) pass.

## 6. Running

Requires a GeN-Foam build sourced into the shell.

```bash
# group constants (needs OpenMC + ENDF/B-VIII.0)
cd genfoam/lattice && python triga_pin.py && python extract_mgxs.py && cd ../..
python3 genfoam/tools/openmc2genfoam.py genfoam/lattice/mgxs_2g_data.h5 \
    genfoam/triga_steady/constant/neutroRegion/nuclearData

# steady state (builds the mesh, then runs GeN-Foam to t = 100 s)
genfoam/triga_steady/Allrun
```

The transient restarts from the steady solution at t = 100 s: copy the steady
case's mesh and its `100/` time directory into `triga_transient_rod/`, then
run `genfoam/triga_transient_rod/Allrun`.
