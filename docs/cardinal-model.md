# Cardinal model: methods, verification and results

The Monte Carlo side of the TRIGA Mark I cross-code study: continuous-energy
OpenMC neutronics, coupled to MOOSE heat conduction through Cardinal, with a
NekRS coolant model. The problem definition is in
[`specification.md`](specification.md); the cross-code comparison is in
[`../results/comparison/COMPARISON.md`](../results/comparison/COMPARISON.md).

## 1. Models

| Model | Geometry | Boundaries | Purpose |
|---|---|---|---|
| Unit cell | 2-D square pin cell, pitch 4.235 cm | reflective | k-infinity; fuel temperature coefficient |
| Heterogeneous core (primary) | Explicit 12 × 12 square lattice truncated by a 49.5 cm × 60 cm cylinder; 120 fuelled positions | vacuum | k-effective, leakage, pin powers |
| Homogenised core | Same cylinder, volume-weighted smear | vacuum | Separates geometry treatment from solution method in the comparison |
| Coupled pin | 3-D single pin, 60 cm, OpenMC ↔ MOOSE (Picard) | reflective radially, vacuum axially | Average-pin fuel and clad temperatures with feedback |
| Coolant subchannel | NekRS LES, Re = 4755, 2880 elements, order 7 | inlet/outlet, symmetry on lateral faces | Coolant field (diagnostic only, see §7) |

Thermal scattering: `c_H_in_ZrH` and `c_Zr_in_ZrH` on fuel, `c_H_in_H2O` on
water. These are essential for a hydride-moderated core.

## 2. Software and data

| Component | Version |
|---|---|
| Cardinal | `snapshot-20-10-27-54609-g8b05495ce0` |
| OpenMC (solver, embedded in Cardinal) | `v0.15.3-190-g66359e5dd` |
| OpenMC Python API (input generation only) | `0.15.1.dev0` |
| MOOSE | moose-libmesh 2026.06.05, moose-petsc 3.25.2, MPICH |
| Nuclear data | ENDF/B-VIII.0 HDF5, `cross_sections.xml` SHA-256 `ba7f6d5a371b5a8d…` (coupled run: ENDF/B-VII.1) |
| Neutronics platform | Apple M2, 8 cores, 8 GiB, macOS |
| Coupled / GPU platform | Ubuntu 24.04, Xeon Gold 6136, 92 GiB, NVIDIA GTX 1080 Ti |

Every OpenMC run writes its seed, particle and batch counts, OpenMC version,
nuclear-data checksum, platform, wall clock and timestamp into its CSV row
in `results/cardinal/`.

## 3. Neutronics results

Production runs: 20,000,000 histories (40,000 particles × 500 batches, 100
inactive), ENDF/B-VIII.0, 293 K.

| Quantity | Model | Value |
|---|---|---|
| **k-infinity** | 2-D unit cell, reflective | **1.384207 ± 0.000214** (21 pcm) |
| **k-effective** | 3-D bare heterogeneous core | **1.102059 ± 0.000260** (26 pcm) |
| k-effective | 3-D bare homogenised core (H in H₂O kernel) | 1.145259 ± 0.000737 |
| Leakage fraction | bare core | 0.20149 ± 0.00012 |
| Pin power peak/average | 120 pins | 2.2544 |
| Peak / average power density | bare core | 6.595 / 2.165 W/cm³ |

### 3.1 Statistical convergence

| Configuration | Histories | k-infinity | σ (pcm) |
|---|---|---|---|
| smoke | 40,000 | 1.378230 | 498 |
| baseline | 2,500,000 | 1.383854 | 60 |
| **production** | **20,000,000** | **1.384207** | **21** |

All three agree within their uncertainties.

**Seed repeatability** (unit cell, baseline, 5 seeds): mean 1.384100, sample
standard deviation 72 pcm against a reported per-run σ of about 60 pcm, so the
reported uncertainty is credible. Core production with seeds 11 and 21:
1.102008 and 1.102059, a 5 pcm difference.

Source convergence was checked with Shannon entropy on every run
(`results/cardinal/entropy/`).

### 3.2 Physics consistency checks

These are internal consistency checks, not experimental validation.

| Check | Result |
|---|---|
| Unit-cell leakage | 0.00000: reflective boundaries correct |
| Volume fractions / fuel weight fractions | sum to 1.00000 / 100.000% |
| Σ pin powers | 250,000.0 W, matching the specified power exactly |
| Axial power symmetry residual | 0.0069: symmetric within statistics |
| k∞ × (1 − leakage) vs k_eff | 1.3842 × 0.7985 = 1.1053 vs 1.1021, consistent to 0.3% |
| Pin peak/average | 2.2544, consistent with bare-cylinder Bessel peaking (about 2.3) |

### 3.3 Two post-processing defects found and fixed

1. **Mesh index transposition.** The cylindrical mesh tally was reshaped as
   (r, φ, z), but OpenMC orders bins with r varying fastest. Both shapes are
   valid for a 10 × 20 mesh, so no error was raised. The axial-symmetry check
   caught it: the profile was asymmetric (2527 W vs 6375 W at mirror-image
   ends) in a geometry symmetric by construction. After the fix the residual is
   0.0069 and the mesh peak/average fell from a spurious 7.27 to 3.05. The
   symmetry check is now permanent.
2. **Unweighted average power density.** The core average was first a plain
   mean over mesh cells, over-weighting the small inner rings. It is now
   volume-weighted and reproduces the analytic 250 kW / 115,467 cm³ =
   2.165 W/cm³.

Neither defect affected k. The pin peaking factor uses a separate distribcell
tally and was unaffected.

### 3.4 Power distribution

| Quantity | Value |
|---|---|
| Peak pin power | 4696.62 W |
| Average pin power | 2083.33 W |
| Pin peak/average | 2.2544 |
| Relative uncertainty, hottest pin | 0.26% |

The square lattice is cut by the cylindrical envelope, so peripheral
positions hold only a sliver of fuel (the minimum is 0.036 of the average).
Averaging over these depresses the mean, so 2.2544 is an **upper estimate** of
the whole-pin peaking factor.

## 4. Homogenisation study

A single smeared zone cannot represent hydrogen correctly: about 56% of the
hydrogen is bound in ZrH and 44% in H₂O, but OpenMC allows each nuclide only
one thermal-scattering table per material. The error was bracketed rather
than hidden (baseline statistics):

| Hydrogen kernel | k-effective | σ (pcm) |
|---|---|---|
| all H as H-in-ZrH | 1.132505 | 68 |
| all H as H-in-H₂O | 1.145259 | 74 |
| free gas | 1.136651 | 79 |

The spread is **1275 pcm**, more than twice the acceptance criterion.
Homogenisation also raises k by about 3900 pcm relative to the heterogeneous
lattice, the expected loss of spatial self-shielding in the U-238 resonances.
The **heterogeneous lattice** is therefore the primary core model.

## 5. Fuel temperature coefficient

Fuel temperature swept from 296 to 1000 K with the moderator held at 293 K,
isolating fuel feedback. On the unit cell this gives the lattice (k∞)
coefficient; repeated on the bare core it includes the leakage feedback that
governs a real transient. Uncertainties are 1σ from Monte Carlo statistics.

| Band (K) | k∞ coefficient (pcm/K) | k_eff coefficient (pcm/K) | Leakage share |
|---|---|---|---|
| 296–400 | −5.08 ± 0.43 | −6.31 ± 0.73 | 20% |
| 400–500 | −6.24 ± 0.46 | −9.12 ± 0.78 | 32% |
| 500–600 | −7.76 ± 0.47 | **−10.79 ± 0.82** | 28% |
| 600–800 | −6.78 ± 0.23 | −10.61 ± 0.42 | 36% |
| 800–1000 | −5.92 ± 0.24 | −9.10 ± 0.44 | 35% |

The coefficient is large and negative, and grows in magnitude as the fuel
heats from room temperature. Both features identify hydride physics rather
than U-238 Doppler alone (a UO₂ LWR pin gives roughly −2 to −3 pcm/K). Heating
the hydride up-scatters thermal neutrons off the ~0.14 eV ZrH oscillator,
hardening the spectrum; in a finite core the harder spectrum also leaks more,
so the leakage term reinforces the lattice feedback. Both curves suggest a
maximum magnitude between about 500 and 800 K; the turnover is resolved at
roughly the 2σ level only.

Data: `results/cardinal/fuel_temperature_coefficient.csv`,
`core_temperature_coefficient.csv`, `leakage_feedback.csv`.

## 6. Coupled neutronics–conduction (OpenMC ↔ MOOSE)

Average pin, 2083.33 W (250 kW / 120 pins). Cell-averaged fission power goes
to MOOSE; cell temperatures return to OpenMC. 20,000 particles, 150 batches
(30 inactive), 10 Picard iterations, 6400-element solid mesh, ENDF/B-VII.1.

| Quantity | Value |
|---|---|
| Coupled k-effective | 1.30662 ± 0.00055 |
| Average / maximum fuel temperature | 330.39 / 359.00 K |
| Average / maximum clad temperature | 322.28 / 336.15 K |
| Integrated pin heating | 2083.33 W (exact conservation) |
| Wall clock | 2905 s |

**Verification against an analytic solution.** The cylindrical-conduction
hand calculation predicts a peak fuel temperature of 362.8 K; Cardinal gives
359.0 K, **1.1% apart**. The residual is explained by the computed axial
power shape being flatter than the cosine the hand calculation assumes.
Temperature is continuous across the fuel–clad interface.

**Library sensitivity.** The same coupled model run on ENDF/B-VIII.0 (macOS
arm64, 5k particles) and ENDF/B-VII.1 (Ubuntu x86, 20k particles) gives
k = 1.30561 and 1.30656, an offset of **+73 pcm**, and maximum fuel
temperatures 0.25 K apart. Average fuel temperature agrees to 7 × 10⁻⁴ K
across the two platforms.

### Thermal-hydraulic assumptions

The specification gives no thermal transport properties, so these are
documented modelling choices:

| ID | Quantity | Value | Basis | Share of peak rise |
|---|---|---|---|---|
| T1 | Fuel conductivity | 18 W/m·K | Published U-ZrH₁.₆₅ data (roughly constant 17–20 W/m·K) | 35% |
| T2 | Clad conductivity | 16 W/m·K | SS304 near 300–400 K | 2% |
| T3 | Film coefficient | 1098 W/m²·K | Dittus–Boelter at Re = 4755, Pr = 7.01, D_h = 2.387 cm | **63%** |
| T4 | Coolant bulk rise | 3.567 K over 60 cm, linear | Energy balance at 0.2 m/s and 2083.33 W | — |
| T5 | Pin power | 2083.33 W | 250 kW / 120 pins (average pin) | — |

T3 is the weakest link: Re = 4755 is transitional, below the range where
Dittus–Boelter is reliable, and it is a tube correlation applied to a
rod-in-square subchannel. It controls most of the temperature rise, which is
why the NekRS coolant model was attempted.

## 7. Coolant CFD (NekRS): preliminary diagnostic only

A NekRS implicit LES of the coolant subchannel (Re = 4755, 2880 spectral
elements, polynomial order 7, 1.47 M points) ran on an NVIDIA GTX 1080 Ti.
What it establishes:

- The CUDA path works end to end (exit code 0, about 2.7 GB device memory).
- The flow field converges: mass imbalance is flat at 0.12% from step 1400.

What it does **not** establish:

- A conservation check after the run found that only **59%** of the clad
  surface carried the heated-wall boundary tag in the committed mesh. The mesh
  generator and a runtime wall-area check (abort above 1% error) have been
  fixed, but the mesh has not yet been regenerated and rerun.
- The 20,000-step run covered only 1.17 flow-through times, with 34.6% energy
  closure, and shows a filter undershoot below the inlet temperature
  (291.5 K vs 293 K).

The NekRS temperatures are therefore **not used** in any result or
comparison. Coupled coolant temperatures come from assumption T3/T4 instead.

## 8. Limitations

1. **Bare core.** No reflector or control rods (per the specification), so the
   model leaks 20% and does not describe a physical TRIGA at criticality.
2. **Average pin.** Coupled temperatures describe an average pin; the hot pin
   is about 2.25× higher in power.
3. **Film coefficient is a correlation** used outside its reliable range.
4. **NekRS not production-qualified** (see §7) and not in the coupling chain.
5. **Library deviation** in the coupled run (VII.1, +73 pcm measured).
6. **OpenMC version** is 0.15.3-dev rather than 0.16.0.
7. **No mesh or polynomial-order refinement study** for the conduction or CFD
   meshes.
8. **No experimental validation.** All checks are internal consistency or
   code-to-code.
