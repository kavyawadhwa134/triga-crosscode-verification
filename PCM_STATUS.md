# pcM Status

Last updated: 2026-09-12

## Completed

- **Phase 0 — Environment audit.** Cardinal, NekRS, MOOSE, OpenMC, MPI, and
  ENDF/B-VIII.0 located and version-checked. Hardware recorded from the actual
  machine. NekRS backend determined empirically from `CMakeCache.txt`, not
  assumed. Written to `spec/hardware.md`.
- **Phase 1 — Scientific input audit.** Approved problem definition transcribed
  into `spec/geometry.md`, `spec/materials.md`, `spec/operating.md`. Every
  missing or ambiguous parameter flagged rather than filled in from pcL.
- **Phase 2 — Model scope selected and justified** (`spec/operating.md`).
- Git repository initialized; `.gitignore` excludes large generated outputs per
  the project protocol Git Rules.
- Independence record written (`spec/independence.md`).

## Current

Standalone OpenMC and the Binder OpenMC-MOOSE average-pin production run are
complete. NekRS has passed a separate 1,000-step CUDA diagnostic on a GTX
1080 Ti, but its temperature field was not yet energy-balanced and it was not
coupled to OpenMC/MOOSE. Current work is the standalone NekRS production run,
followed by the three-way coupling implementation.

## Blocked

Nothing hard-blocking. The neutronics ran to completion.

Two answers are needed before the **core** numbers can be called final:
- **Q1** (core diameter vs radius) — the core was run on pcM's provisional
  diameter reading. If that reading is wrong, every core result changes.
- **Q4** (homogenized vs heterogeneous, and which hydrogen S(α,β) kernel) —
  worth ≈3100 pcm and ≈1275 pcm respectively.

The **unit-cell** k-infinity result depends on neither and is final.

## Independent Assumptions

Full detail in the spec files; summary:

| ID | Assumption | Impact |
|---|---|---|
| A1 | Natural Zr isotopics in fuel | small |
| A3 | S(α,β) `c_H_in_ZrH`/`c_Zr_in_ZrH` applied to fuel | **large** — essential for hydride fuel |
| A5/A6 | SS304 density 8.00 g/cm³ and standard composition (not in spec) | tens of pcm |
| A7 | Pure light water, no boron | small |
| A8 | S(α,β) `c_H_in_H2O` applied to water | **large** |
| G1 | No fuel/clad gap (spec gives only two radii) | small on k; matters for thermal |
| G2 | No Zr central rod (spec gives solid fuel meat) | ~100 pcm |
| G5 | Core homogenization by unit-cell volume fractions | **large** |
| G6 | Bare core, no reflector (vacuum BC as specified) | **large** — departs from physical TRIGA |
| O4 | Atmospheric pressure | sets saturation temperature |
| O5 | +0.5 $ transient treated as out of baseline scope | scope question |

Provisional geometry interpretation: core = cylinder, **diameter** 0.495 m ×
height 0.60 m (see Q1).

## Files Created/Changed

```
.gitignore
PCM_STATUS.md
spec/{hardware,geometry,materials,operating,independence}.md
cardinal/openmc/{materials,geometry,settings,tallies,run,postprocess}.py
scripts/{env.sh,run_openmc.sh}
results/PCM_RESULTS.md
results/pcm_openmc_{unitcell,core,core_homog}.csv
results/pcm_power_{summary,radial,axial}_core.csv
results/pcm_pin_power_core.csv
results/{README.md,validation_step2.csv,validation_step5.csv,validation_step6.csv}
results/validation_nekrs_gpu_diagnostic.csv
results/pcm_coupled_production{,_openmc}_vii1.csv
results/paraview_pcm_*.png
results/pcm_results_figures.pdf
```

## Commands Executed

```bash
git init
sw_vers; sysctl -n machdep.cpu.brand_string hw.ncpu hw.physicalcpu hw.memsize hw.model; uname -m
/Users/kavyawadhwa/MOOSE/cardinal/cardinal-opt --version
/Users/kavyawadhwa/Anaconda/anaconda3/envs/openmc/bin/python -c "import openmc; print(openmc.__version__)"
git -C /Users/kavyawadhwa/MOOSE/cardinal/contrib/openmc describe --tags
grep -E 'ENABLE_(CUDA|HIP|OPENCL|METAL|DPCPP)' /Users/kavyawadhwa/MOOSE/cardinal/build/nekrs/CMakeCache.txt
```

## Tests

Software verification: OpenMC executes, 16 runs completed, no crashes.

Numerical verification:
- Particle/batch convergence (unit cell): smoke/baseline/production agree
  within uncertainty; production σ = 21 pcm.
- Seed repeatability (unit cell, 5 seeds): scatter 72 pcm vs reported σ 60 pcm
  — consistent, no hidden bias.
- Seed repeatability (core, 2 seeds): 5 pcm apart.

Physics verification:
- Unit-cell leakage exactly 0 (reflective BCs correct).
- Pin powers sum to 250,000.0 W (normalization correct).
- Axial power profile symmetric to 0.69 % (geometry is symmetric by
  construction).
- k_inf × (1 − leakage) = 1.1053 vs directly computed k_eff = 1.1021 (0.3 %).

Two post-processing defects were found and fixed; both are documented in
`results/PCM_RESULTS.md` §5.1 rather than quietly corrected:
1. Cylindrical mesh tally reshaped as (r, φ, z) when OpenMC orders bins
   (z, φ, r) — silently transposed radius and height. Caught by the symmetry
   check. Did not affect k.
2. Core-average power density computed as an unweighted cell mean instead of
   volume-weighted.

## Results

Production, 20 M histories, ENDF/B-VIII.0, 293 K:

| Quantity | Value |
|---|---|
| k-infinity (2-D unit cell, reflective) | 1.384207 ± 0.000214 |
| k-effective (bare heterogeneous core, vacuum) | 1.102059 ± 0.000260 |
| Leakage fraction | 0.20149 ± 0.00012 |
| Pin peak/average (120 pins) | 2.2544 (upper estimate) |
| Peak / average power density | 6.595 / 2.165 W/cm³ |

Homogenized-core bracket (baseline statistics): k_eff = 1.132505 (H-in-ZrH),
1.145259 (H-in-H₂O), 1.136651 (free gas) — a ≈1275 pcm spread caused by a
genuine OpenMC restriction (one S(α,β) table per nuclide per material) that
makes a fully smeared core physically ill-posed here. pcM's reported core
value is the heterogeneous one.

Fuel and clad temperatures are now available from the two-way OpenMC-MOOSE
production run. Coupled coolant velocity, pressure, temperature, and turbulence
fields remain unavailable until NekRS production and three-way coupling finish.

Binder OpenMC-MOOSE production, ENDF/B-VII.1, 10 Picard iterations:

| Quantity | Value |
|---|---|
| Final k-effective | 1.3066210577542 ± 0.00055 |
| Average / maximum fuel temperature | 330.390708 / 358.995333 K |
| Average / maximum clad temperature | 322.278940 / 336.145067 K |
| Integrated pin heating | 2083.33 W |
| Runtime | 2905.49 s |

Full report: `results/PCM_RESULTS.md`.

## Runtime

| Run | Wall clock |
|---|---|
| Unit cell production (20 M) | 456 s |
| Core production (20 M) | 365–446 s |
| Unit cell baseline (2.5 M) | 44 s |
| Core baseline (2.5 M) | 38 s |
| Binder OpenMC-MOOSE production (10 Picard iterations) | 2905.49 s |
| Standalone NekRS CUDA diagnostic (1000 steps) | 319.21 s |

Cold OpenMC timings used 8 OpenMP threads on the Apple M2. The coupled and
NekRS timings used the Binder Xeon/GTX 1080 Ti environment; the NekRS
diagnostic was an intentional serial fallback because the available MPI
launcher produced singleton processes.

## Next Step

1. Resolve the Binder CUDA runtime path and finish the 2,000-step standalone
   NekRS production run.
2. Verify mass and energy balance and extract coolant temperature, velocity,
   pressure, and turbulence outputs.
3. Implement and smoke-test three-way OpenMC-MOOSE-NekRS coupling.
4. Run production, post-process, and provide the independent pcM package to the
   supervisor for comparison.

Answers to Q1 and Q4 are needed before the core result can be considered
final; the unit-cell result does not depend on them.

## Questions for Supervisor

**Q1 — Core geometry (blocking for Model 2).** "Single zone 0.495 × 0.60 m" is
ambiguous. Is 0.495 m the core **diameter** or the **radius**, and is the zone a
cylinder or a rectangular slab? pcM's provisional reading is a cylinder of
diameter 0.495 m × height 0.60 m, because at the specified 4.235 cm pitch that
gives ≈107 fuel positions — the right order for a TRIGA Mark I. A radius of
0.495 m would imply ≈429 elements, which is not a Mark I. Confirm before pcM
runs the core case.

**Q2 — OpenMC version deviation.** The spec names OpenMC **0.16.0**. This
machine has none: Cardinal's embedded solver is **v0.15.3-190-g66359e5dd** and
the Python API is **0.15.1.dev0**. Is running on 0.15.3 acceptable for the
benchmark, or must 0.16.0 be installed first? This is a reproducibility
question, not a physics one, but the spec said "reproduce exactly."

**Q3 — SS304 definition.** Density and composition are not in the spec. pcM
assumed 8.00 g/cm³ with standard SS304 composition. Confirm or supply the
approved values.

**Q4 — Homogenization and reflector for the core model.** Should the single
zone be smeared using the unit-cell volume fractions (pcM's default), and is
the core genuinely **bare** with vacuum boundaries — i.e. no graphite
reflector? A bare TRIGA core is a large departure from the physical reactor,
so pcM wants this confirmed as intentional rather than assumed.

**Q5 — Is the +0.5 $ transient in scope?** PCM_WORKFLOW.md defines a
steady-state production run and no transient phase, but the approved conditions
mention a +0.5 $ insertion. Confirm whether pcM should produce a transient
result set as well.

**Note on independence.** pcL's results were disclosed to pcM in the same
message as the approved conditions. This is recorded in
`spec/independence.md`, together with pcM's commitment not to tune toward them
and not to perform the pcL↔pcM comparison. pcM will report its own numbers
whatever they are.
