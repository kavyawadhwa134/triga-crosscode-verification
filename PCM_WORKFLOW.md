# PCM_WORKFLOW.md --- Independent pcM Simulation Workflow

## Mission

pcM must independently simulate the approved TRIGA Mark I problem using
Cardinal/OpenMC/NekRS/MOOSE.

**Do not use pcL simulation files or results.**

The pcM workflow ends when an independently reproducible result set is
produced and reported to the supervisor.

The supervisor performs the cross-code comparison afterward.

------------------------------------------------------------------------

# Phase 0 --- Environment Audit

## 0.1 Verify Cardinal

``` bash
conda activate cardinal
which cardinal-opt
cardinal-opt --version
python -c "import openmc; print('openmc', openmc.__version__)"
```

## 0.2 Verify NekRS

``` bash
ls "$CONDA_PREFIX/bin" | grep -i nek
```

Determine whether the installed NekRS backend can use the Mac GPU.

Do not assume GPU acceleration.

## 0.3 Record Hardware

Run:

``` bash
sw_vers
sysctl -n machdep.cpu.brand_string
sysctl -n hw.ncpu
sysctl -n hw.memsize
sysctl -n hw.model
system_profiler SPDisplaysDataType
```

Record the actual results in:

`spec/hardware.md`

## Gate

Do not begin expensive modelling until the environment is understood.

------------------------------------------------------------------------

# Phase 1 --- Scientific Input Audit

Inspect ONLY the approved project specification.

Read:

``` text
spec/geometry.md
spec/materials.md
spec/operating.md
```

Do NOT inspect pcL implementation files for missing information.

Determine:

-   reactor/model scope;
-   geometry;
-   materials;
-   operating temperature;
-   power;
-   boundary conditions;
-   nuclear-data library;
-   energy groups;
-   other approved assumptions.

If a required value is missing:

1.  document it;
2.  identify exactly what is needed;
3.  ask the supervisor.

Do not obtain it from pcL.

## Gate

The scientific problem definition must be sufficiently specified before
production modelling.

------------------------------------------------------------------------

# Phase 2 --- Choose pcM Model Scope

Because pcM is a Mac and NekRS is expected to be CPU-only, choose the
smallest scientifically meaningful model.

Preferred order:

### Option A --- Unit Cell

A TRIGA fuel-element/unit-cell model.

### Option B --- Symmetry Sector

A physically justified symmetry sector.

### Option C --- Full Core

Only if hardware testing demonstrates that it is computationally
practical and scientifically necessary.

Document:

-   selected scope;
-   justification;
-   symmetry assumptions;
-   omitted regions;
-   expected limitations.

Record in:

`spec/operating.md`

## Gate

The scope must answer the intended scientific question without requiring
an unnecessarily expensive calculation.

------------------------------------------------------------------------

# Phase 3 --- Cardinal Tutorial Validation

Run the relevant Cardinal tutorials in sequence:

1.  standalone OpenMC;
2.  MGXS generation;
3.  standalone NekRS;
4.  OpenMC + MOOSE conduction;
5.  NekRS + OpenMC coupling.

For each tutorial record:

-   tutorial;
-   command;
-   runtime;
-   exit status;
-   important warnings/errors;
-   reusable implementation pattern.

Record timings in:

`spec/hardware.md`

## Gate

A capability should be demonstrated in a known working example before
adapting it to TRIGA.

------------------------------------------------------------------------

# Phase 4 --- Build Independent OpenMC Model

Create pcM's own OpenMC implementation.

Recommended structure:

``` text
cardinal/openmc/
├── materials.py
├── geometry.py
├── settings.py
├── tallies.py
├── run.py
└── postprocess.py
```

Use the approved scientific specification.

Do not copy pcL OpenMC files.

## Required baseline

Run a standalone k-eigenvalue calculation.

Extract:

-   `k_eff`;
-   `k_eff` statistical uncertainty;
-   normalized power;
-   relevant spatial/region power.

Write compact results to:

`results/pcm_openmc_baseline.csv`

Also save enough metadata to reproduce the calculation.

------------------------------------------------------------------------

# Phase 5 --- OpenMC Verification

Check:

-   geometry validity;
-   material definitions;
-   source convergence;
-   statistical uncertainty;
-   power normalization;
-   physically reasonable power distribution.

Where practical, perform basic sensitivity/convergence checks:

-   particle count;
-   active batches;
-   inactive batches;
-   random seed/repeatability.

Do not change the model merely to produce a desired `k_eff`.

## Gate

The standalone OpenMC result must be credible before coupling work.

------------------------------------------------------------------------

# Phase 6 --- Independent MGXS Generation

Generate the required few-group constants independently using pcM's
OpenMC setup.

Use the approved nuclear-data library and group structure.

Document:

-   energy boundaries;
-   number of groups;
-   tally method;
-   material/region mapping;
-   normalization;
-   statistical treatment.

If GeN-Foam compatibility requires a converter, implement it only as an
interface tool. It must not require pcL data.

For any converter, test it using pcM-generated MGXS data.

## Gate

The MGXS data must be traceable to pcM's own OpenMC calculation.

------------------------------------------------------------------------

# Phase 7 --- Independent MOOSE Thermal Model

Build the thermal model corresponding to the approved pcM geometry.

Depending on the approved scope:

-   resolved fuel/clad;
-   or scientifically justified homogenization.

Implement:

-   thermal properties;
-   heat source;
-   interfaces;
-   boundary conditions;
-   convergence criteria.

Run the thermal model independently before full coupling where
practical.

Record:

-   maximum temperature;
-   average temperature;
-   temperature profile;
-   runtime;
-   convergence.

------------------------------------------------------------------------

# Phase 8 --- Independent NekRS Model

Build the fluid model corresponding to the same approved geometry.

Target the relevant physics:

-   buoyancy;
-   low-speed flow;
-   natural convection;
-   heated surfaces;
-   coolant temperature;
-   velocity;
-   pressure.

Build the appropriate `.re2` and `.par` files according to the installed
NekRS/Cardinal version and working tutorials.

## Test order

``` text
mesh
 ↓
boundary conditions
 ↓
standalone flow
 ↓
thermal behavior
 ↓
runtime
```

Do not couple until the standalone model is understood.

------------------------------------------------------------------------

# Phase 9 --- Cardinal Coupling

Create the Cardinal master input.

Use the installed Cardinal examples as the syntax reference.

Target coupling:

``` text
OpenMC
  ↕
MOOSE
  ↕
NekRS
```

Implement appropriate:

-   MultiApps;
-   Transfers;
-   Picard iterations;
-   relaxation;
-   convergence criteria;
-   power-to-thermal coupling;
-   temperature-to-neutronics feedback.

Do not invent Cardinal syntax when an installed tutorial can establish
the correct form.

------------------------------------------------------------------------

# Phase 10 --- Coupled Smoke Test

Run a deliberately small calculation:

-   low OpenMC particle count;
-   small model;
-   few Picard iterations;
-   short runtime.

Verify:

1.  Cardinal initializes;
2.  OpenMC initializes;
3.  MOOSE initializes;
4.  NekRS initializes;
5.  data transfers occur;
6.  power reaches the thermal system;
7.  temperature returns to neutronics;
8.  coupling iterations behave sensibly;
9.  convergence logic operates.

## Gate

Production is forbidden until the smoke test succeeds or a documented
reason establishes that a specific component cannot yet be coupled.

------------------------------------------------------------------------

# Phase 11 --- Numerical Convergence

Before production conclusions, perform reasonable convergence checks.

Depending on computational budget:

### OpenMC

-   particle/batch sensitivity.

### NekRS

-   mesh sensitivity;
-   timestep sensitivity where applicable.

### MOOSE

-   mesh sensitivity;
-   nonlinear/linear convergence.

### Cardinal

-   coupling iteration/relaxation sensitivity.

Record the chosen settings and justification.

------------------------------------------------------------------------

# Phase 12 --- Production Steady-State Simulation

Run the approved production model.

Record:

-   wall-clock time;
-   hardware;
-   CPU usage where practical;
-   memory behavior where practical;
-   convergence.

Extract:

-   `k_eff`;
-   uncertainty;
-   normalized power distribution;
-   regional power;
-   fuel temperature;
-   clad temperature;
-   coolant temperature;
-   velocity;
-   pressure;
-   convergence history.

Write compact derived data to:

`results/`

Do not commit huge raw simulation outputs.

------------------------------------------------------------------------

# Phase 13 --- Independent Result Package

Create:

`results/PCM_RESULTS.md`

Include:

## Model

-   geometry;
-   scope;
-   materials;
-   operating conditions.

## Software

-   macOS;
-   Cardinal;
-   OpenMC;
-   NekRS;
-   MOOSE;
-   relevant dependencies.

## Nuclear Data

-   library;
-   release;
-   checksum;
-   group structure.

## Numerical Setup

-   particle counts;
-   batches;
-   mesh;
-   timestep;
-   coupling iterations;
-   convergence tolerances;
-   relaxation.

## Results

Report actual values:

-   `k_eff ± uncertainty`;
-   power metrics;
-   maximum fuel temperature;
-   maximum clad temperature;
-   coolant temperature;
-   velocity/pressure metrics;
-   runtime.

## Limitations

Explicitly document:

-   model reduction;
-   CPU-only NekRS;
-   unresolved physics;
-   numerical limitations;
-   missing experimental validation.

------------------------------------------------------------------------

# Phase 14 --- Supervisor Handoff

When pcM is complete, provide the supervisor with:

1.  `results/PCM_RESULTS.md`
2.  relevant CSVs;
3.  exact reproduction commands;
4.  commit hash;
5.  software versions;
6.  model assumptions;
7.  actual numerical results;
8.  known limitations.

Do NOT calculate or claim pcL-vs-pcM agreement.

The supervisor will independently compare the two result sets.

------------------------------------------------------------------------

# Phase 15 --- Final Definition of Done

``` text
[ ] Environment verified
[ ] Hardware documented
[ ] Scientific specification verified
[ ] Model scope justified
[ ] Cardinal tutorials tested
[ ] Independent OpenMC model implemented
[ ] OpenMC baseline completed
[ ] OpenMC result checked
[ ] Independent MGXS generated if required
[ ] MOOSE thermal model tested
[ ] NekRS model tested
[ ] Cardinal coupling implemented
[ ] Coupled smoke test passes
[ ] Numerical convergence checked
[ ] Production steady-state run completed
[ ] Results extracted
[ ] PCM_RESULTS.md completed
[ ] Reproduction commands documented
[ ] Git commits pushed
[ ] Results handed to supervisor
```

------------------------------------------------------------------------

# Absolute Boundary

The pcM workflow must remain:

``` text
APPROVED SCIENTIFIC SPECIFICATION
             ↓
       INDEPENDENT pcM
             ↓
        CARDINAL RUN
             ↓
       PCM RESULTS
             ↓
          SUPERVISOR
             ↓
     pcL ↔ pcM COMPARISON
```

Never:

``` text
pcL result → tune pcM → reproduce pcL
```

The value of this project depends on the independence of the two
calculations.
