# pcM Results — Neutronics and Two-Way Coupling (Interim)

**Status: INTERIM.** Standalone OpenMC neutronics and a Binder
OpenMC-MOOSE average-pin production calculation are complete. A separate
NekRS CUDA diagnostic has also executed successfully, but NekRS is not yet
part of the coupled calculation. Consequently, fuel and clad temperatures are
available; coupled coolant temperature, velocity, pressure, and turbulence
fields are not.

Generated 2026-09-12 by pcM, independently of pcL. No pcL file or result was
used as an input; see `spec/independence.md`.

## Binder OpenMC-MOOSE production update

The Binder production case completed 10 Picard iterations using
ENDF/B-VII.1 in 2,905.49 s. Its final state is:

| Quantity | Value |
|---|---|
| Coupled k-effective | 1.3066210577542 ± 0.00055 |
| Maximum tally relative error | 0.00834775 |
| Average / maximum fuel temperature | 330.390708 / 358.995333 K |
| Average / maximum clad temperature | 322.278940 / 336.145067 K |
| Integrated average-pin heating | 2083.33 W |

This is a two-way OpenMC-MOOSE result. Its coolant heat-transfer coefficient
and bulk-temperature rise are imposed surrogates; it is not the final
thermal-hydraulic result. Standardized supervisor-facing tables and figures are
listed in `results/README.md`.

---

## 1. Headline results

| Quantity | Model | Value | Uncertainty |
|---|---|---|---|
| **k-infinity** | 2-D unit cell, reflective | **1.384207** | ± 0.000214 (21 pcm) |
| **k-effective** | 3-D bare heterogeneous core, vacuum | **1.102059** | ± 0.000260 (26 pcm) |
| Leakage fraction | bare core | 0.20149 | ± 0.00012 |
| Pin power peak/average | bare core, 120 pins | 2.2544 | — |
| Peak power density | bare core | 6.595 W/cm³ | — |
| Average power density | bare core | 2.165 W/cm³ | — |

Both production runs: 20,000,000 histories (40,000 particles × 500 batches,
100 inactive), ENDF/B-VIII.0, 293 K.

**pcM does not compare these to pcL.** Per the project protocol and PCM_WORKFLOW.md
Phase 14, the cross-code comparison is the supervisor's task.

---

## 2. Model

### 2.1 Unit cell (k-infinity)

Square-pitch TRIGA cell, 2-D (axially reflective, zero axial leakage).

| Parameter | Value |
|---|---|
| Fuel outer radius | 1.815 cm |
| Clad outer radius | 1.866 cm |
| Pitch | 4.235 cm |
| Boundaries | reflective on all faces |
| Fuel / clad / water volume fraction | 0.57701 / 0.03290 / 0.39009 |

No fuel–clad gap and no Zr central rod: the specification gives exactly two
radii and a solid fuel meat (assumptions G1, G2).

### 2.2 Core (k-effective) — pcM's primary core model

Bare cylinder, **heterogeneous**: an explicit 12×12 square lattice of the
specified pin, truncated by the core cylinder. 120 lattice positions are
fuelled.

| Parameter | Value |
|---|---|
| Core diameter | 49.5 cm (**provisional reading — see §7 Q1**) |
| Core height | 60.0 cm |
| Boundaries | vacuum (radial, top, bottom) |
| Reflector | none (bare, per specification — assumption G6) |
| Fuelled pins | 120 |

### 2.3 Materials

| Material | Density | Composition |
|---|---|---|
| Fuel U-ZrH₁.₆₅ | 6.0 g/cm³ | U-235 1.7, U-238 6.8, Zr 89.862, H-1 1.638 wt% |
| Clad SS304 | 8.00 g/cm³ *(assumed)* | Fe bal., Cr 19.0, Ni 9.25, Mn 2.0, Si 1.0, C 0.08 wt% *(assumed)* |
| Coolant | 1.0 g/cm³ | H₂O, no boron |

Thermal scattering: `c_H_in_ZrH` + `c_Zr_in_ZrH` on fuel, `c_H_in_H2O` on
water. These are essential for a hydride-moderated core, not optional.

### 2.4 Operating conditions

250 kW thermal, 293 K, coolant inlet 0.2 m/s (used by the not-yet-built
thermal-fluid model), atmospheric pressure assumed.

---

## 3. Software and data

| Component | Version |
|---|---|
| OpenMC solver | 0.15.4-dev190, commit `66359e5dd8382b81c508458fa64922100627fa89` (Cardinal's build) |
| OpenMC Python API | 0.15.1.dev0 (input generation only) |
| Cardinal | `snapshot-20-10-27-54609-g8b05495ce0` |
| MOOSE | exercised in the Binder OpenMC-MOOSE production run |
| NekRS | standalone CUDA diagnostic completed; not yet coupled |
| Nuclear data | ENDF/B-VIII.0 HDF5, `cross_sections.xml` SHA-256 (first 16) `ba7f6d5a371b5a8d` |
| Primary cold runs | macOS 26.6.2, Apple M2, 8 cores, 8 GiB RAM, arm64 |
| Coupled/GPU runs | Ubuntu 24.04, Xeon Gold 6136, 92 GiB, GTX 1080 Ti |

**Specification deviation:** the spec names OpenMC **0.16.0**; that version is
not installed on this machine. See §7 Q2.

---

## 4. Numerical setup and convergence

| Configuration | Particles | Batches (inactive) | Histories |
|---|---|---|---|
| smoke | 1,000 | 40 (10) | 40,000 |
| baseline | 10,000 | 250 (50) | 2,500,000 |
| production | 40,000 | 500 (100) | 20,000,000 |

### 4.1 Particle/batch convergence (unit cell)

| Configuration | k-infinity | σ (pcm) |
|---|---|---|
| smoke | 1.378230 | 498 |
| baseline | 1.383854 | 60 |
| **production** | **1.384207** | **21** |

All three agree within their uncertainties. k is converged with respect to
particle count at the production setting.

### 4.2 Seed repeatability (unit cell, baseline, 5 seeds)

| Seed | k-infinity | σ (pcm) |
|---|---|---|
| 1 | 1.383854 | 60 |
| 2 | 1.385280 | 59 |
| 3 | 1.384114 | 62 |
| 4 | 1.383340 | 61 |
| 5 | 1.383910 | 54 |

Mean 1.384100, sample standard deviation **72 pcm** against a reported
per-run σ of ~60 pcm. The observed scatter is consistent with the reported
statistical uncertainty, so the uncertainty estimate is credible and no hidden
bias is evident.

### 4.3 Seed repeatability (core, production)

| Seed | k-effective | σ (pcm) |
|---|---|---|
| 11 | 1.102008 | 25 |
| 21 | 1.102059 | 26 |

Difference 5 pcm — well inside statistics.

---

## 5. Physics verification

These are consistency checks, **not** experimental validation. No experimental
or reference data has been used (project protocol verification hierarchy: level 3
only; levels 4 and 5 not performed).

| Check | Result | Verdict |
|---|---|---|
| Unit-cell leakage | 0.00000 ± 0.00000 | Pass — reflective boundaries correct |
| Volume fractions sum | 1.00000 | Pass |
| Fuel weight fractions sum | 100.000 % | Pass |
| Power normalization: Σ pin powers | 250,000.0 W | Pass — matches specified 250 kW exactly |
| Axial power symmetry residual | 0.0069 | Pass — symmetric to within statistics |
| k_inf × (1 − leakage) vs k_eff | 1.3842 × 0.7985 = 1.1053 vs 1.1021 | Pass — consistent to ~0.3 % |
| Pin peak/average | 2.2544 | Plausible — bare-cylinder radial Bessel peaking is ≈2.3 |
| Axial profile shape | symmetric, cosine-like | Plausible for a bare core |
| Radial profile shape | Bessel-like, edge-depressed | Plausible for a bare core |

### 5.1 Two post-processing defects found and fixed

Recorded because the project protocol forbids hiding failed calculations.

1. **Mesh index transposition.** The cylindrical mesh tally was reshaped as
   (r, φ, z), but OpenMC orders mesh bins with **r varying fastest**, i.e.
   (z, φ, r). Both shapes are numerically valid for a 10×20 mesh, so no error
   was raised — the radius and height axes were silently swapped. It was caught
   by an axial-symmetry check: the profile was asymmetric (2527 W vs 6375 W at
   mirror-image ends) in a geometry that is symmetric by construction. After
   the fix the residual is 0.0069. The mesh peak/average changed from a
   spurious 7.27 to 3.05. A permanent symmetry check is now part of
   post-processing.
2. **Unweighted average power density.** The core average was first computed as
   a plain mean over mesh cells, which over-weights the small inner rings of a
   cylindrical mesh. It is now volume-weighted (total power ÷ total volume),
   which reproduces the analytic 250 kW / 115,467 cm³ = 2.165 W/cm³.

Neither defect affected k. The per-pin peaking factor (§6) uses a separate
distribcell tally and was unaffected by both.

---

## 6. Power distribution

Per-pin power via a distribcell tally — mesh-independent, and the quantity to
use for comparison.

| Quantity | Value |
|---|---|
| Fuelled pins | 120 |
| Peak pin power | 4696.62 W |
| Average pin power | 2083.33 W |
| **Pin peak/average** | **2.2544** |
| Pin min/average | 0.0361 |
| Σ pin power | 250,000.0 W |
| Relative uncertainty, hottest pin | 0.00262 |

**Caveat on the peaking factor.** The lattice is truncated by the core
cylinder, so peripheral lattice positions contain only a sliver of fuel. The
minimum pin at 0.0361 of average is such a sliver, not a physically cold pin.
Because the average is taken over all 120 fuelled positions including these
truncated ones, it is depressed relative to a whole-pin average, and 2.2544 is
therefore an **upper estimate** of the true pin peaking factor. A
volume-normalized peaking factor would be modestly lower. This is a
consequence of the specified bare-cylinder envelope cutting a square lattice,
and is reported rather than tuned away.

A cylindrical-mesh peak/average is also reported (3.0460) but is
mesh-resolution dependent and is **not** the recommended comparison metric:
the cylindrical mesh is not aligned with the square lattice, so individual
cells straddle fuel and water.

Profiles: `results/pcm_power_radial_core.csv`, `results/pcm_power_axial_core.csv`,
`results/pcm_pin_power_core.csv`.

---

## 7. Homogenization study (secondary)

The specification describes the core as a "single zone", which implies a
homogenized smear. pcM ran this too, and found a **hard physics obstacle**:

Hydrogen in this core exists in two distinct bound states — H in ZrH (≈56 % of
all hydrogen) and H in H₂O (≈44 %) — but OpenMC permits each nuclide to appear
in only **one** thermal-scattering table per material. A single smeared zone
therefore cannot represent both kernels, and neither state dominates. There is
no correct single choice.

pcM bracketed the error rather than picking one silently (baseline statistics,
2.5 M histories):

| Hydrogen kernel | k-effective | σ (pcm) |
|---|---|---|
| all H as H-in-ZrH | 1.132505 | 68 |
| all H as H-in-H₂O | 1.145259 | 74 |
| free gas (no S(α,β)) | 1.136651 | 79 |

Spread: **≈1275 pcm**. In addition, homogenization raises k by **≈3100 pcm**
relative to the heterogeneous lattice (1.1325 vs 1.1012), which is the expected
loss of spatial self-shielding in the U-238 resonances.

**Consequence:** pcM reports the **heterogeneous lattice** result
(k_eff = 1.102059) as its core value, because it is free of this defect. If
the benchmark intends a homogenized single zone, the supervisor should say
which hydrogen kernel is prescribed — the choice is worth over 1200 pcm.

---

## 8. Runtime

| Run | Histories | Wall clock |
|---|---|---|
| Unit cell, production | 20 M | 456 s |
| Core, production | 20 M | 365–446 s |
| Unit cell, baseline | 2.5 M | 44 s |
| Core, baseline | 2.5 M | 38 s |

8 OpenMP threads, 1 MPI rank, Apple M2. Calculation rate ≈ 53,000
particles/second (unit cell, active batches).

---

## 9. Limitations

1. **No coupled coolant thermal-hydraulics yet.** Fuel and clad temperatures
   are available from MOOSE, but the coolant condition is still an imposed
   surrogate. Coupled coolant temperature, velocity, pressure, and turbulence
   fields are absent rather than estimated.
2. **Cold, clean, isothermal at 293 K.** No temperature feedback, no Doppler,
   no thermal expansion, no burnup, no xenon, no control rods, no burnable
   poison.
3. **Bare core.** No graphite reflector, per the specification's vacuum
   boundaries. A physical TRIGA Mark I is reflected, so this model leaks far
   more (20 %) and is much less reactive than the real reactor. This is a
   specification-faithful idealization, not a model of the actual machine.
4. **Provisional core geometry.** The 0.495 m dimension is read as a diameter;
   if it is a radius, every core number here changes. See Q1.
5. **SS304 assumed.** Density and composition are not in the specification.
6. **No Zr central rod, no fuel–clad gap** — spec-faithful, but both depart
   from the physical element.
7. **OpenMC version deviates** from the specified 0.16.0.
8. **No experimental validation.** Nothing here has been compared with
   measured data. Section 5 checks are internal consistency only.
9. **NekRS execution is not yet production-qualified.** The Apple M2 remains
   CPU-only. The Binder GTX 1080 Ti CUDA path completed a 1,000-step standalone
   diagnostic and a 2,000-step continuation, but MPI launched singleton
   processes and only 59.03% of the clad surface retained heated-wall boundary
   ID 1. Those NekRS fields are invalid for physical use. The mesh generator
   now preserves the complete wall and the UDF aborts when wall area differs
   from the analytic value by more than 1%; a regenerated `fluid.re2` and rerun
   are required.

---

## 10. Reproduction

```bash
git clone <pcM repo> && cd pcm
source scripts/env.sh

./scripts/run_openmc.sh unitcell production --seed 11
./scripts/run_openmc.sh core     production --seed 21

source scripts/env.sh && "$PCM_PYTHON" cardinal/openmc/postprocess.py \
    run/core_production_seed21/statepoint.500.h5 --label core
```

Convergence and repeatability studies:

```bash
for s in 1 2 3 4 5; do ./scripts/run_openmc.sh unitcell baseline --seed $s; done
for k in zrh h2o none; do ./scripts/run_openmc.sh core_homog baseline --sab $k; done
```

Data files: `results/pcm_openmc_unitcell.csv`,
`results/pcm_openmc_core.csv`, `results/pcm_openmc_core_homog.csv`,
`results/pcm_power_summary_core.csv`, `results/pcm_pin_power_core.csv`,
`results/pcm_power_radial_core.csv`, `results/pcm_power_axial_core.csv`.

Every run records its own seed, particle count, batch counts, OpenMC version,
nuclear-data checksum, platform, wall clock, and timestamp in its CSV row.

---

## 11. Open questions blocking completion

See `PCM_STATUS.md` for the full list. The two that affect the numbers above:

- **Q1** Is 0.495 m the core diameter or radius, and is the zone a cylinder or
  a slab? All §1 core values are provisional on the diameter reading.
- **Q4** Is the core intended to be homogenized or heterogeneous, and if
  homogenized, which hydrogen thermal-scattering kernel is prescribed? Worth
  ≈3100 pcm and ≈1275 pcm respectively.
