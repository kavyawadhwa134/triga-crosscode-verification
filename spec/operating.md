# pcM Operating Conditions & Model Scope

Source: approved problem definition supplied by the supervisor 2026-09-12.

## Operating conditions

| Parameter | Value | Source |
|---|---|---|
| Reactor thermal power | 250 kW | approved spec |
| Reference temperature | 293 K | approved spec |
| Coolant inlet velocity | 0.2 m/s | approved spec |
| Core boundary condition (neutronics) | vacuum | approved spec |
| Unit-cell boundary condition | reflective | approved spec |

### Energy-group structure (for MGXS, Phase 6)

| Group | Range |
|---|---|
| 1 (fast) | 0.625 eV – 20 MeV |
| 2 (thermal) | 0 – 0.625 eV |

Two groups, thermal cutoff 0.625 eV, per the approved specification.

### Assumptions (documented)

- **O1** 293 K applies to all materials in the cold baseline: fuel, clad, and
  coolant. The spec gives a single temperature.
- **O2** 0.2 m/s is the coolant **inlet** velocity for the thermal-fluid model.
  The spec does not state a flow direction; pcM assumes upward axial flow
  (natural-circulation orientation for a pool-type TRIGA).
- **O3** Coolant inlet temperature = 293 K.
- **O4** System pressure is not specified. pcM assumes atmospheric
  (0.1 MPa), consistent with an open-pool TRIGA Mark I and with ρ_water = 1.0
  g/cm³ at 293 K. Impact: sets the saturation temperature (≈373 K), which
  matters for judging whether local boiling is predicted.
- **O5** Steady state is the production target. The approved message also
  mentions a **+0.5 $ reactivity insertion transient**. PCM_WORKFLOW.md
  Phase 12 specifies a *steady-state* production run and lists no transient
  phase. pcM therefore treats the transient as **out of baseline scope** and
  will ask the supervisor whether it is required. It is not silently skipped.

---

## Model scope decision (PCM_WORKFLOW.md Phase 2)

### Constraint

From `spec/hardware.md`: Apple M2, **8 cores, 8 GiB RAM**, and **NekRS is
CPU-only** (no CUDA/HIP/Metal/OpenCL compiled). 8 GiB of shared memory is the
hard limit — a full-core CFD mesh with OpenMC tallies and MOOSE fields resident
simultaneously will not fit, and CPU-only NekRS on 8 cores makes a full-core
transient infeasible in any reasonable wall-clock time.

### Decision

pcM adopts, in the workflow's preferred order:

1. **Option A — Unit cell** for the neutronics baseline and for the coupled
   Cardinal demonstration. This is the model the spec itself defines in
   greatest detail (exact radii, pitch, reflective BCs), it is the k-infinity
   reference point, and it is tractable on 8 CPU cores.
2. **Homogenized single-zone core** for the k-effective calculation. The spec
   defines this as a single homogenized zone with vacuum BCs, which is cheap in
   OpenMC — no fine lattice, no per-pin tallies — and therefore affordable even
   on this hardware.

**Option C (full core, heterogeneous, coupled) is rejected** on hardware
grounds, consistent with the project protocol's instruction to select a scientifically
defensible reduced model when hardware makes a full-core coupled model
impractical.

### Justification

- The unit cell answers the k-infinity question exactly as specified, with no
  approximation beyond those the spec itself makes.
- The homogenized core answers the k-effective and leakage question as
  specified.
- The thermal-fluid coupling (MOOSE + NekRS) is demonstrated on the unit-cell
  geometry, where a single heated pin in an axial channel is a well-posed
  natural/forced-convection problem that fits in memory.

### Documented limitations of this scope

- No pin-by-pin power distribution in the core model — it is homogenized by
  specification, so a heterogeneous peaking factor is not resolvable from the
  core model alone.
- 2-D unit cell has no axial leakage and no axial power shape.
- Bare core (no reflector, vacuum BCs) departs from the physical
  graphite-reflected TRIGA Mark I — see `spec/geometry.md` G6.
- CPU-only NekRS limits mesh refinement; the mesh-sensitivity study in
  Phase 11 will be bounded by wall-clock, and that bound will be reported.

### Gate status

Scope selected and justified. Proceeding to Phase 3 (Cardinal tutorial
validation) and Phase 4 (independent OpenMC model).
