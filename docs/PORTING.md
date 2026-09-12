# Moving pcM to another machine

pcM was developed on an 8 GiB Apple M2 (macOS, CPU-only NekRS). That machine
ran out of memory during NekRS setup, which is why the work is being moved.
This document is what you need to reproduce pcM elsewhere, and it records the
memory failure in enough detail that it is not repeated.

Nothing here depends on pcL.

---

## 1. What you need on the target machine

| Component | Purpose | Required for |
|---|---|---|
| Cardinal (built, with `cardinal-opt`) | driver for everything | all phases |
| OpenMC Python API | writes the input XML | all phases |
| ENDF/B-VIII.0 HDF5 + thermal `S(a,b)` | nuclear data | all phases |
| MPI (`mpirun`) + working `mpifort` | NekRS JIT-builds Fortran at run time | NekRS only |
| `exo2nek` | Exodus -> `.re2` mesh | only to regenerate the mesh |

`fluid.re2` is committed, so `exo2nek` is only needed if the fluid mesh changes.

> `mpifort` must actually work, not merely exist. On a conda MOOSE install it
> wraps a toolchain compiler (`x86_64-conda-linux-gnu-gfortran` on Linux,
> `arm64-apple-darwin*-gfortran` on macOS) that lives in the env's `bin`. If
> that directory is not on `PATH`, the NekRS build dies partway through with
> `command not found`. `scripts/env.sh` adds it automatically; the audit script
> verifies it.

---

## 2. Getting set up

```bash
git clone <this repo> pcm && cd pcm
./scripts/audit_environment.sh
```

The audit auto-detects Cardinal, conda, Python, nuclear data, NekRS, the
Fortran toolchain and any GPU, then prints what is missing. Override anything
it gets wrong before sourcing:

```bash
export PCM_CARDINAL_DIR=$HOME/cardinal
export PCM_CROSS_SECTIONS=$HOME/nuclear_data/endfb-viii.0-hdf5/cross_sections.xml
export PCM_MOOSE_ENV=moose          # conda env holding the MOOSE toolchain
```

Nothing else in the repo hardcodes a path.

---

## 3. Running

```bash
./scripts/run_openmc.sh unitcell baseline      # standalone neutronics
./scripts/run_coupled.sh smoke                 # OpenMC <-> MOOSE, ~2 min
./scripts/run_coupled.sh production 8          # better statistics, 8 ranks
./scripts/run_nekrs.sh 8                       # standalone fluid, 8 ranks
```

Reproduce the TRIGA temperature-coefficient check with:

```bash
$PCM_PYTHON cardinal/openmc/temperature_coefficient.py --config baseline
```

---

## 4. The memory failure, and how to avoid repeating it

**This is the single most important thing to carry over.**

NekRS does not simply load a mesh. At startup it **JIT-compiles a Nek5000
interface**, and Nek5000 uses *compile-time static allocation* — array sizes
are baked into a generated `SIZE` file, not allocated at run time.

The generated `SIZE` contained:

```
parameter (lelg=2880)     ! total elements
parameter (lpmin=1)       ! MPI ranks
parameter (lelt=2880)     ! elements PER RANK
```

`lelt` is elements **per rank**. NekRS was launched on **one** rank, so
`lelt = lelg` — the entire mesh statically allocated in a single process.
Nek5000's headers declare ~**854 arrays** shaped `(lx1,ly1,lz1,lelt)`. At
`lx1 = 6` each is 6³ × 2880 = 622,080 doubles = 5.0 MB:

> **854 × 5.0 MB ≈ 4.25 GB of static data in one compilation unit.**

`gfortran` was killed materialising that, on the two files that include the
full COMMON-block set:

```
make: *** [obj/nekInterface.o] Terminated: 15
make: *** [obj/fluid.o]        Terminated: 15
```

`Terminated: 15` is SIGTERM — the process was killed, not a compiler error.
75 of 104 objects had already built.

### Sizing table

`lelt = ceil(elements / ranks)`; static memory per rank `≈ 854 × lx1³ × lelt × 8` bytes.

| Elements | Ranks | lelt | Per rank | All ranks |
|---|---|---|---|---|
| 2880 | 1 | 2880 | **4.25 GB** | 4.25 GB | ← what failed |
| 2880 | 4 | 720 | 1.06 GB | 4.25 GB |
| 2880 | 8 | 360 | 0.53 GB | 4.25 GB |
| 1440 | 4 | 360 | 0.53 GB | 2.13 GB |
| 720 | 4 | 180 | 0.27 GB | 1.06 GB |

### Rules

1. **Never run NekRS on one rank.** `scripts/run_nekrs.sh` refuses `< 2`.
2. **Ranks fix the compile, not the total.** Static arrays are per-process, so
   the right-hand column is unchanged by adding ranks. If total RAM is the
   binding constraint, shrink the mesh or lower `polynomialOrder`, don't just
   add ranks.
3. **Delete `.cache` when changing rank count.** A stale cache carries the old
   `lelt`. The run script does this.
4. **Do not run jobs concurrently on a small machine.** The original failure
   had a coupled OpenMC+MOOSE job running at the same time.
5. **Check real headroom, not nominal RAM.** The 8 GiB machine already held
   ~3 GB compressed and ~1.7 GB swap from ordinary desktop apps before any
   solver started — true headroom was ~4 GB, not 8.

### Consequences on a bigger machine

With more RAM the 2880-element mesh is comfortable and `polynomialOrder` can
rise from 5 toward the 7 used in Cardinal's `tutorials/turbulence/les` case,
which targets Re = 5000 — very close to pcM's Re = 4755. That matters
scientifically: at 2880 elements / order 5 the LES is under-resolved and can
only be reported as a coupling demonstration, not converged turbulence.

If the target machine has an NVIDIA GPU, `env.sh` sets
`PCM_NEKRS_BACKEND=CUDA` automatically once `nvidia-smi` reports a device.
**Verify NekRS was actually built with CUDA before claiming GPU acceleration**
— per the project protocol, do not assume a backend that has not been demonstrated.

---

## 5. Re-record the environment

`spec/hardware.md` describes the Apple M2. The hardware constraint drove the
model-scope decision in `spec/operating.md` (unit cell rather than full core),
so on a larger machine that decision **should be revisited rather than
inherited**. Append a new section for the new machine; do not silently
overwrite the old one — the existing results were produced under the old
constraint.

---

## 6. State at the time of the move

Complete and verified:

- Standalone OpenMC neutronics — `k_inf`, `k_eff`, power distributions
- Coupled Cardinal OpenMC <-> MOOSE conduction — max fuel 358.8 K, max clad
  336.0 K, power conservation exact, within 1.1% of an analytic solution
- TRIGA fuel temperature coefficient — −6.34 pcm/K over 296–1000 K, confirming
  ZrH feedback rather than plain U-238 Doppler
- NekRS mesh pipeline — `exo2nek` built, `fluid.re2` generated, non-dimensional
  flux scaling verified exactly (predicted outlet T\* = 1.00000)

Not done:

- Coolant temperature, velocity, pressure — needs the NekRS run
- Better-converged coupled production run — the smoke test carries ~2% tally
  relative error
- Three-way OpenMC <-> MOOSE <-> NekRS coupling

Placeholders that NekRS is meant to replace (`spec/thermal.md`): the convective
boundary condition `h = 1098 W/m²·K` from Dittus-Boelter at Re = 4755, and the
3.567 K bulk coolant rise from an energy balance.
