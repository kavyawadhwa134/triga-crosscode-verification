# Reproducing the Cardinal calculations

How to set up and run the Cardinal (OpenMC / MOOSE / NekRS) side of the
study. The GeN-Foam side is described in [`genfoam-model.md`](genfoam-model.md).

## 1. Requirements

| Component | Needed for | Notes |
|---|---|---|
| Cardinal with `cardinal-opt` | coupled runs, NekRS | built from source |
| OpenMC Python API | writing inputs | `import openmc` must work |
| ENDF/B-VIII.0 HDF5 with `c_H_in_ZrH`, `c_Zr_in_ZrH`, `c_H_in_H2O` | everything | several GB |
| MPI and a working `mpifort` | NekRS only | see §5 |

Versions used for the committed results:

- Cardinal `snapshot-20-10-27-54609-g8b05495ce0`
- OpenMC solver `v0.15.3-190-g66359e5dd` (embedded in Cardinal; the Python API,
  `0.15.1.dev0`, only writes input files)
- MOOSE `moose-libmesh 2026.06.05`, `moose-petsc 3.25.2`, MPICH

Hardware actually used:

| Work | Machine |
|---|---|
| Standalone neutronics | Apple M2, 8 cores, 8 GiB, macOS (NekRS CPU-only) |
| Coupled run, NekRS | Ubuntu 24.04, Xeon Gold 6136, 92 GiB, NVIDIA GTX 1080 Ti |

| Tier | RAM | What is possible |
|---|---|---|
| Neutronics | ≥ 4 GiB | standalone OpenMC |
| Coupled | ≥ 16 GiB | OpenMC + MOOSE; NekRS only with a reduced mesh |
| Full | ≥ 32 GiB | everything, including NekRS at order 7 |

## 2. Setup

```bash
./scripts/audit_environment.sh
```

`scripts/env.sh` auto-detects Cardinal, conda, Python, nuclear data and any
NVIDIA GPU on macOS and Linux. Override anything it gets wrong before running:

```bash
export TRIGA_CARDINAL_DIR=/path/to/cardinal
export TRIGA_CROSS_SECTIONS=/path/to/endfb-viii.0-hdf5/cross_sections.xml
export TRIGA_MOOSE_ENV=moose
export TRIGA_CORES=16
```

The audit prints `OK` / `MISSING` per component and a NekRS memory-sizing
table.

## 3. Running

```bash
# standalone neutronics (configs: smoke, baseline, production)
./scripts/run_openmc.sh unitcell production --seed 11     # k-infinity
./scripts/run_openmc.sh core     production --seed 21     # k-effective
source scripts/env.sh && "$TRIGA_PYTHON" cardinal/openmc/postprocess.py \
    run/core_production_seed21/statepoint.500.h5 --label core

# fuel temperature coefficient (the TRIGA signature check)
"$TRIGA_PYTHON" cardinal/openmc/temperature_coefficient.py --config baseline

# coupled OpenMC <-> MOOSE
./scripts/run_coupled.sh smoke              # 5 Picard steps, ~2 min
./scripts/run_coupled.sh production 8       # 10 Picard steps, 8 ranks

# standalone NekRS (never on one rank; see §5)
./scripts/run_nekrs.sh 8
```

Convergence and repeatability studies:

```bash
for s in 1 2 3 4 5; do ./scripts/run_openmc.sh unitcell baseline --seed $s; done
for k in zrh h2o none; do ./scripts/run_openmc.sh core_homog baseline --sab $k; done
```

`temperature_coefficient.py` sweeps the unit cell. The bare-core sweep in
`results/cardinal/core_temperature_coefficient.csv` applied the same procedure
to the heterogeneous core model; that driver is not yet included in the
repository.

Results are written to `results/cardinal/`; each CSV row records its seed,
statistics, code version, nuclear-data checksum, platform and wall clock.

To regenerate the NekRS mesh (needed before any further CFD run, see
[`cardinal-model.md`](cardinal-model.md) §7):

```bash
cd cardinal/nekrs
cardinal-opt -i fluid.i --mesh-only
cardinal-opt -i convert.i --mesh-only && mv convert_in.e convert.exo
printf '1\nconvert\n0\n0\nfluid\n' | exo2nek
```

## 4. Expected results (regression targets)

| Quantity | Value |
|---|---|
| k-infinity, unit cell, production | 1.384207 ± 0.000214 |
| k-effective, bare core, production | 1.102059 ± 0.000260 |
| Leakage fraction | 0.20149 ± 0.00012 |
| Pin peak/average | 2.2544 |
| Fuel temperature coefficient, 296–1000 K average (unit cell) | −6.34 pcm/K |
| Coupled maximum fuel temperature | 359.0 K |
| Coupled power integral | 2083.33 W (exact) |

**If the temperature coefficient comes out small or positive, the S(α,β)
data is missing or mis-bound.** `c_H_in_ZrH` is tabulated from 296 K, below
which the 293 K reference temperature sits, so the OpenMC settings use
interpolation with a widened tolerance.

## 5. Known pitfalls

**NekRS single-rank memory.** NekRS JIT-compiles a Nek5000 interface with
compile-time static arrays sized by elements *per rank*. On one rank the
2880-element mesh puts about 854 arrays × 5 MB ≈ 4.25 GB into a single
compilation unit, and the compiler is killed (this happened on the 8 GiB
development machine).

| Elements | Ranks | Per rank | All ranks |
|---|---|---|---|
| 2880 | 1 | 4.25 GB | 4.25 GB (fails) |
| 2880 | 8 | 0.53 GB | 4.25 GB |
| 1440 | 4 | 0.53 GB | 2.13 GB |
| 720 | 4 | 0.27 GB | 1.06 GB |

Never run NekRS on one rank (the script refuses). More ranks fix the compile
but not the total; if total RAM binds, reduce the mesh or the polynomial
order. Delete `.cache` when changing the rank count.

**`mpifort` toolchain.** On conda MOOSE installs `mpifort` wraps a compiler in
the environment's `bin`; if that is not on `PATH` the NekRS build fails part
way. `env.sh` adds it and the audit checks it.

**Tutorial constants.** Cardinal's LWR tutorials were used only as input
syntax references. This must return nothing:

```bash
grep -rniE '0\.39218|0\.45720|3000e6|zircaloy|uo2|573\.15' cardinal/
```

**Exodus element types.** The annular mesh centre is `PRISM6` and the rest
`HEX8`; they must stay in separate blocks (`fuel`, `fuel_center`).
