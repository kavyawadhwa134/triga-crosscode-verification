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

Phase 3 — Cardinal tutorial validation, then Phase 4 — independent OpenMC
unit-cell model.

## Blocked

Nothing hard-blocking. Four items need supervisor input but do not stop the
unit-cell work (see *Questions for Supervisor*). The core-geometry ambiguity
(Q1) **does** block the Model-2 core calculation.

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
spec/hardware.md
spec/geometry.md
spec/materials.md
spec/operating.md
spec/independence.md
cardinal/{openmc,moose,nekrs,coupling}/   (empty, scaffolded)
results/                                   (empty)
scripts/                                   (empty)
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

None yet. Phase 3 tutorial runs are next; they are the first software
verification evidence.

## Results

None yet. No k has been computed by pcM.

## Runtime

Phase 0–2: a few minutes, no compute-intensive work.

## Next Step

1. Run Cardinal's standalone OpenMC tutorial to confirm the toolchain executes
   (Phase 3 software verification).
2. Build the independent OpenMC unit-cell model (`cardinal/openmc/`) and run
   the k-infinity baseline (Phase 4).
3. Resolve the OpenMC Python-API / solver version split before trusting any
   number (see Q2).

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
