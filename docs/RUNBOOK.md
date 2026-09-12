# pcM Runbook — TRIGA Mark I, Cardinal / OpenMC / NekRS / MOOSE

**Audience:** an engineer setting this up and
running it on a machine that is not the one it was developed on.

**You are expected to adapt Part 3 (environment) to your platform.**
Parts 1, 2 and 7 are fixed and must not be adapted. Read Part 7 before
changing anything.

This runbook is self-contained. You do not need any prior conversation.

---

# Part 1 — What this project is, and the one rule that matters most

pcM is an **independent** simulation of a TRIGA Mark I research reactor built
on the Cardinal ecosystem (OpenMC neutronics + MOOSE heat conduction + NekRS
CFD).

A second, separate team ("pcL") is independently simulating **the same
reactor** using a different code (GeN-Foam). A supervisor will later compare
the two result sets. The entire scientific value of the exercise depends on
the two calculations being produced without reference to each other.

## The independence rule — ABSOLUTE

**You must not read, copy, import, consult, or be influenced by anything from
pcL.** That includes pcL's GeN-Foam case, mesh, nuclear data, OpenMC inputs,
`k_eff`, tuned parameters, output CSVs, or results of any kind.

Specifically:

- **Never tune a pcM parameter to make pcM agree with pcL.**
- **Never use a pcL number as an input, a check, or a sanity target.**
- If pcM's result looks "wrong," diagnose it from physics, not by comparison.
- If you are blocked and the only way forward appears to be looking at pcL,
  **stop and report the blocker instead.**
- **Do not compute or state pcL-vs-pcM agreement.** That is the supervisor's
  job, performed after both are finished.

Only the *scientific problem definition* in Part 2 is shared between the two
teams. The implementation must be independent.

## Scientific integrity rules

1. Never fabricate a result.
2. Never invent a missing parameter silently — document any assumption, why it
   is needed, its source, and its expected impact.
3. Solver convergence is **not** physical validation. Keep these separate:
   software verification → numerical convergence → physics verification →
   cross-code comparison → experimental validation.
4. Never claim experimental validation. There is no experimental data here.
5. Never hide a failed calculation. Report failures.
6. Never silently change geometry, nuclear data, or energy groups.
7. If a result is physically implausible, say so rather than reporting it.

---

# Part 2 — Scientific specification (FIXED — do not modify)

These values come from the approved problem definition. They are the shared
input. Changing any of them invalidates the comparison.

## Geometry

| Parameter | Value |
|---|---|
| Fuel outer radius | 1.815 cm |
| Clad outer radius | 1.866 cm |
| Lattice pitch | 4.235 cm, square |
| Unit-cell boundary condition | reflective (all lateral faces) |
| Core | single zone, 0.495 m diameter × 0.60 m height |
| Core boundary condition | vacuum |

There is **no fuel–clad gap**: clad inner radius = fuel outer radius = 1.815 cm.
Derived: fuel 57.701 vol%, clad 3.290 vol%, water 39.009 vol%.

## Materials

| Material | Density | Composition |
|---|---|---|
| Fuel U-ZrH₁.₆₅ | 6.0 g/cm³ | U-235 1.7, U-238 6.8, Zr 89.862, H-1 1.638 wt% |
| Clad SS304 | 8.00 g/cm³ *(assumed)* | Fe bal., Cr 19.0, Ni 9.25, Mn 2.0, Si 1.0, C 0.08 wt% *(assumed)* |
| Coolant | 1.0 g/cm³ | H₂O, no boron |

**Thermal scattering `S(α,β)` is mandatory:** `c_H_in_ZrH`, `c_Zr_in_ZrH`,
`c_H_in_H2O`. Without `c_H_in_ZrH` the defining TRIGA physics is absent and
every result is wrong. See Part 6, Trap 3.

## Operating conditions

| Parameter | Value |
|---|---|
| Thermal power | 250 kW |
| Reference temperature | 293 K |
| Coolant inlet velocity | 0.2 m/s |
| Pressure | atmospheric, 0.1 MPa *(assumed — open-pool TRIGA)* |
| Energy groups (for MGXS) | 2 groups, thermal cutoff 0.625 eV |

## Nuclear data

**ENDF/B-VIII.0, official release, HDF5 format.** Not a substitute library.
Changing the library invalidates the comparison.

---

# Part 3 — Environment (ADAPT THIS PART TO YOUR PLATFORM)

## 3.1 Required components

| Component | Needed for | Notes |
|---|---|---|
| Cardinal, built, with `cardinal-opt` | everything | must be compiled; no package exists |
| OpenMC Python API | generating input XML | `import openmc` must work |
| ENDF/B-VIII.0 HDF5 + thermal `S(α,β)` | everything | several GB |
| MPI (`mpirun`) and a **working** `mpifort` | NekRS only | see Part 6, Trap 2 |
| `exo2nek` | only to regenerate the fluid mesh | `fluid.re2` is committed |

Reference versions the results in Part 5 were produced with:

- Cardinal `snapshot-20-10-27-54609-g8b05495ce0`
- OpenMC solver `v0.15.3-190-g66359e5dd` (embedded in Cardinal — **this is the
  solver**; the Python API is only used to write input files)
- OpenMC Python API `0.15.1.dev0`
- MOOSE `moose-libmesh 2026.06.05`, `moose-petsc 3.25.2`, mpich

## 3.2 FEASIBILITY GATE — check this before attempting anything

Measure the target environment, then pick a tier. **Do not skip this.** The
development machine (8 GiB) died mid-run; see Part 6, Trap 1.

| | RAM | Cores | What is actually possible |
|---|---|---|---|
| **Tier 3 — Full** | ≥ 32 GiB | ≥ 8 | Everything, including NekRS LES and 3-way coupling |
| **Tier 2 — Coupled** | ≥ 16 GiB | ≥ 4 | OpenMC + MOOSE conduction; NekRS only with a reduced mesh |
| **Tier 1 — Neutronics** | ≥ 4 GiB | ≥ 2 | Standalone OpenMC only (Phases 4–5). No NekRS. |
| **Tier 0 — Not viable** | < 4 GiB | any | Do not attempt. Report the constraint. |

Measure, don't assume. In a container use `nproc` and `free -g`; the audit
script reports both and sizes NekRS accordingly.

### If the target is Binder or a similar container-based environment

**Cardinal has already been installed and run on Binder for this project**, so
treat the install as a solved problem and work from the existing image
definition rather than rebuilding from scratch.

What still needs checking, because a container hides it:

1. **Measure the actual limits inside the container**, not the advertised ones:

   ```bash
   nproc; free -g; ulimit -v; df -h /tmp
   ```

   `scripts/audit_environment.sh` reports cores and memory and prints the NekRS
   sizing table for the numbers it finds. Pick your tier from the measured
   values.

2. **Session lifetime is the real constraint.** Coupled and NekRS runs take
   tens of minutes and an idle timeout will kill them mid-run. Run long jobs
   detached with output to a file, and write results to persistent storage
   rather than container-local `/tmp`, which is lost on restart.

3. **MPI inside containers frequently needs flags.** If `mpirun` refuses to
   start as root or cannot pick a transport, the usual fixes are
   `--allow-run-as-root` (OpenMPI) and forcing a shared-memory/tcp transport.
   NekRS needs a working `mpirun` **and** a working `mpifort` (Part 6, Trap 2).

4. **Confirm the nuclear data is actually present in the image** and that
   `OPENMC_CROSS_SECTIONS` points at it, including the three `S(α,β)` tables.
   If the full ENDF/B-VIII.0 library is too large for the image, fetch only the
   nuclides this model uses — U-235, U-238, Zr isotopes, H-1, O-16,
   Fe/Cr/Ni/Mn/Si/C — plus `c_H_in_ZrH`, `c_Zr_in_ZrH`, `c_H_in_H2O`. Subsetting
   the library this way is acceptable; **substituting a different library is
   not.**

5. **Memory is usually the binding constraint in a container.** Go to Part 6,
   Trap 1 before running NekRS and size the mesh and rank count from measured
   RAM.

If a tier genuinely does not fit, report that rather than substituting a
different code, library, or geometry — that is a correct outcome, not a
failure.

## 3.3 Setup

```bash
git clone <bundle-or-repo> pcm && cd pcm
./scripts/audit_environment.sh
```

`scripts/env.sh` auto-detects Cardinal, conda, Python, nuclear data, NekRS, the
Fortran toolchain and any NVIDIA GPU, on both macOS and Linux. Override
anything it gets wrong **before** sourcing:

```bash
export PCM_CARDINAL_DIR=/path/to/cardinal
export PCM_CROSS_SECTIONS=/path/to/endfb-viii.0-hdf5/cross_sections.xml
export PCM_MOOSE_ENV=moose        # conda env holding the MOOSE toolchain
export PCM_CORES=16               # if auto-detection is wrong
```

The audit prints `OK` / `MISSING` per component and a NekRS memory-sizing
table. **Resolve every `MISSING` that your chosen tier needs before running.**

---

# Part 4 — Running

Always `source scripts/env.sh` first (the scripts do it themselves).

## Phase 4–5 — Standalone OpenMC neutronics (Tier 1+)

```bash
./scripts/run_openmc.sh unitcell baseline      # 2-D unit cell, k-infinity
./scripts/run_openmc.sh core baseline          # 3-D bare core, k-effective
```

Configs are `smoke` (fast, low statistics), `baseline`, `production`.
Outputs land in `results/pcm_openmc_*.csv`.

## TRIGA physics verification — run this, it is the key check

```bash
$PCM_PYTHON cardinal/openmc/temperature_coefficient.py --config baseline
```

Sweeps fuel temperature with the moderator held fixed, isolating the fuel
temperature coefficient. **This is how you demonstrate the model is a TRIGA
and not a generic pincell.** Expected result in Part 5.

## Phase 7–9 — Coupled OpenMC ↔ MOOSE conduction (Tier 2+)

```bash
./scripts/run_coupled.sh smoke                 # 5 Picard steps, ~2 min
./scripts/run_coupled.sh production 8          # 10 Picard steps, 8 ranks
```

Builds the solid mesh if absent, generates the 3-D OpenMC model, runs Cardinal.
Output in `run/coupled_<mode>/`.

## Phase 8 — Standalone NekRS fluid (Tier 2 reduced / Tier 3)

```bash
./scripts/run_nekrs.sh 8                       # 8 MPI ranks
```

**The rank count is not optional — read Part 6, Trap 1 before running this.**
The script refuses fewer than 2 ranks by design; do not remove that guard.

To regenerate the fluid mesh (only if geometry changes):

```bash
cd cardinal/nekrs
cardinal-opt -i fluid.i --mesh-only
cardinal-opt -i convert.i --mesh-only && mv convert_in.e convert.exo
printf '1\nconvert\n0\n0\nfluid\n' | exo2nek
```

## Order of work

Follow this sequence. Do not start an expensive run before its smoke test.

```
audit environment
   → standalone OpenMC → verify (statistics, convergence, temperature coeff)
   → coupled smoke → coupled production
   → standalone NekRS → 3-way coupling
   → convergence checks → production → report
```

---

# Part 5 — Expected results (use as regression targets)

Produced on 8 Apple M2 cores, 8 GiB, CPU-only NekRS, ENDF/B-VIII.0.

## Neutronics

| Quantity | Value | Uncertainty |
|---|---|---|
| k-infinity, 2-D unit cell, reflective | **1.384207** | ± 0.000214 (21 pcm) |
| k-effective, 3-D bare core, vacuum | **1.102059** | ± 0.000260 (26 pcm) |
| Leakage fraction | 0.20149 | ± 0.00012 |
| Pin power peak/average (120 pins) | 2.2544 | — |
| Peak power density | 6.595 W/cm³ | — |

## Fuel temperature coefficient — the TRIGA signature

Moderator fixed at 293 K, fuel temperature swept:

| T_fuel (K) | k_inf | Δρ (pcm) | α (pcm/K) |
|---|---|---|---|
| 296 | 1.384926 | ref | — |
| 400 | 1.374862 | −528 | −5.08 |
| 500 | 1.363166 | −1153 | −5.65 |
| 600 | 1.348904 | −1928 | −6.34 |
| 800 | 1.324688 | −3283 | −6.52 |
| 1000 | 1.304249 | −4466 | −6.34 |

**Average −6.34 pcm/K.** Two features identify this as TRIGA physics rather
than LWR Doppler: the magnitude (a UO₂ LWR pin gives roughly −2 to −3 pcm/K),
and the coefficient becoming *more* negative as fuel heats, which is the
hydrogen-in-ZrH bound-state effect. **If you get a small or positive
coefficient, your `S(α,β)` data is wrong or missing — stop and fix it.**

## Coupled OpenMC ↔ MOOSE (smoke, ~2% tally error)

| Quantity | Value |
|---|---|
| Max fuel temperature | 358.8 K |
| Avg fuel temperature | 330.4 K |
| Max clad temperature | 336.0 K |
| Avg clad temperature | 322.3 K |
| Power integral | 2083.33 W (exact — conservation check) |
| k_eff, 3-D pincell with feedback | ~1.3068 |

Verified against an analytic cylindrical-conduction solution: analytic peak
362.8 K vs computed 358.8 K, **1.1% apart**, the residual explained by the real
axial power shape being flatter than the assumed cosine. Component drops: film
42.4 K, fuel conduction 24.1 K, clad 1.5 K.

## NOT yet produced — these are genuinely absent

- Coolant temperature field, velocity, pressure (NekRS never ran)
- Better-converged coupled production run (smoke carries ~2% tally error)
- Three-way OpenMC ↔ MOOSE ↔ NekRS coupling
- MGXS generation (Phase 6)
- The +0.5 $ reactivity transient (deliberately out of baseline scope)

**Do not report these as done.** If you produce them, say so explicitly and
state the settings used.

## Placeholders NekRS is meant to replace

From `spec/thermal.md` — these are pcM assumptions, not spec values:

- `k_fuel` = 18 W/m·K (U-ZrH₁.₆₅), `k_clad` = 16 W/m·K (SS304)
- `h` = 1098 W/m²·K, Dittus–Boelter at Re = 4755, Pr = 7.01
- Coolant bulk rise 3.567 K, from an energy balance at 0.2 m/s

---

# Part 6 — Known traps

## Trap 1 — NekRS single-rank memory explosion (this killed the dev machine)

NekRS does not merely load a mesh. At startup it **JIT-compiles a Nek5000
interface**, and Nek5000 uses **compile-time static allocation** — array sizes
are baked into a generated `SIZE` file, not allocated at runtime.

Launching on one MPI rank produced:

```
parameter (lelg=2880)     ! total elements
parameter (lpmin=1)       ! MPI ranks
parameter (lelt=2880)     ! elements PER RANK
```

`lelt` is elements **per rank**; with one rank it equals the whole mesh.
Nek5000's headers declare ~**854 arrays** shaped `(lx1,ly1,lz1,lelt)`. At
`lx1=6`, each is 6³ × 2880 = 622,080 doubles = 5.0 MB:

> **854 × 5.0 MB ≈ 4.25 GB of static data in a single compilation unit.**

`gfortran` was killed materialising it:

```
make: *** [obj/nekInterface.o] Terminated: 15
make: *** [obj/fluid.o]        Terminated: 15
```

`Terminated: 15` is SIGTERM — killed, not a compiler error.

`lelt = ceil(elements / ranks)`; static bytes per rank ≈ `854 × lx1³ × lelt × 8`.

| Elements | Ranks | lelt | Per rank | All ranks |
|---|---|---|---|---|
| 2880 | 1 | 2880 | **4.25 GB** | 4.25 GB ← failed |
| 2880 | 4 | 720 | 1.06 GB | 4.25 GB |
| 2880 | 8 | 360 | 0.53 GB | 4.25 GB |
| 1440 | 4 | 360 | 0.53 GB | 2.13 GB |
| 720 | 4 | 180 | 0.27 GB | 1.06 GB |

**Rules:**

1. **Never run NekRS on one rank.** The guard in `run_nekrs.sh` stays.
2. **Ranks fix the compile, not the total.** Static arrays are per-process, so
   the right-hand column does not improve with more ranks. If *total* RAM is
   binding, shrink the mesh or lower `polynomialOrder` — adding ranks will not
   save you.
3. **Delete `.cache` when changing rank count** — a stale cache carries the old
   `lelt`. The script does this.
4. **Never run two solvers concurrently on a small machine.** The original
   failure had a coupled Cardinal job running simultaneously.
5. **Check real headroom, not nominal RAM.** The 8 GiB machine already held
   ~3 GB compressed and ~1.7 GB swap from ordinary desktop apps before any
   solver started. True headroom was ~4 GB.

## Trap 2 — `mpifort` exists but does not work

On conda MOOSE installs `mpifort` wraps a toolchain compiler
(`x86_64-conda-linux-gnu-gfortran` on Linux, `arm64-apple-darwin*-gfortran` on
macOS) living in the env's `bin`. If that directory is not on `PATH`, the NekRS
JIT build dies partway with `command not found` after compiling ~70 files.
`env.sh` adds it; the audit verifies by actually invoking `mpifort -show`.

## Trap 3 — Missing or mis-ranged `S(α,β)` silently destroys the physics

`c_H_in_ZrH` is tabulated from **296 K** upward. The model's 293 K reference is
*below* the first grid point, so OpenMC settings use
`method='interpolation'` with a widened `tolerance` to bind to the nearest
data. If the tolerance is too tight, OpenMC errors; if the tables are absent
entirely, results look plausible but the TRIGA feedback is gone. **Always
confirm with the temperature-coefficient sweep in Part 5.**

## Trap 4 — Do not copy tutorial physics

Cardinal's `lwr_solid` and `pincell_multiphysics` tutorials are used **only as
input-file syntax references**. Their physics is an LWR/SFR pincell and is
wrong here: TRIGA fuel radius is 1.815 cm versus ~0.39 cm, pitch 4.235 cm
versus ~1.26 cm, UO₂/zircaloy versus U-ZrH/SS304, 553 K pressurized versus
293 K pool. Verify no tutorial constants leak in:

```bash
grep -rniE '0\.39218|0\.45720|3000e6|zircaloy|uo2|573\.15' cardinal/
```

This must return nothing.

## Trap 5 — Exodus rejects mixed element types in one block

The annular mesh centre is `PRISM6` while the rest is `HEX8`. They must stay in
separate blocks (`fuel` and `fuel_center`), both treated as fuel. Merging them
fails at write time.

---

# Part 7 — What you may and may not change

## You MAY adapt

- Paths, environment variables, conda/module setup, container definitions
- Rank counts, thread counts, `polynomialOrder`, mesh resolution, batch and
  particle counts — **provided you report the values used**
- Model scope (unit cell / sector / full core) **if** you document the choice
  and its justification
- Installation method for Cardinal, OpenMC, and nuclear data
- Which tier from Part 3.2 you attempt

## You MUST NOT change

- **Anything in Part 2** — geometry, materials, operating conditions, nuclear
  data library, energy-group structure
- **The independence rule in Part 1** — no pcL input, ever
- The `< 2` rank guard in `run_nekrs.sh`
- `S(α,β)` treatment for ZrH

## You MUST report rather than silently work around

Stop and report if:

- A required scientific parameter is missing or two sources conflict
- Geometry or operating conditions are ambiguous
- Nuclear data is unavailable or incomplete
- Cardinal syntax cannot be verified against an installed tutorial
- The NekRS backend is unavailable
- Coupling fails repeatedly without a clear diagnosis
- A result is physically implausible
- The environment cannot support the model (e.g. Binder — see Part 3.2)
- A production run would be computationally excessive
- **You would need pcL data to proceed**

Reporting a blocker is a correct outcome. Substituting a different code,
library, or geometry to produce *a* number is not.

---

# Part 8 — Reporting

Update `PCM_STATUS.md` at each milestone with: Completed / Current / Blocked /
Independent Assumptions / Files Changed / Commands Executed / Tests / Results /
Runtime / Next Step / Questions for Supervisor.

Final deliverable is `results/PCM_RESULTS.md` containing actual numbers:

- `k_eff` ± uncertainty, power distribution
- Fuel, clad, and coolant temperatures
- Velocity and pressure
- Convergence history and wall-clock time
- Software versions, OS, hardware, nuclear data library and checksum
- Particle counts, batches, mesh, timestep, coupling iterations, relaxation
- Exact reproduction commands
- **Limitations**, stated explicitly: model reduction, CPU-only NekRS,
  unresolved physics, numerical limits, and the absence of experimental
  validation

For every number, state which of the five verification levels it has reached
(software / numerical / physics / cross-code / experimental). Do not collapse
them into a single claim of "validated."

**Do not compare against pcL.** Hand the results to the supervisor.
