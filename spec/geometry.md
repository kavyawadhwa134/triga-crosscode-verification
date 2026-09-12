# pcM Geometry Specification

Source: approved problem definition supplied by the supervisor 2026-09-12.

Two models are specified. Both are built independently by pcM.

---

## Model 1 — Unit cell (k-infinity)

| Parameter | Value | Source |
|---|---|---|
| Fuel outer radius | 1.815 cm | approved spec |
| Clad outer radius | 1.866 cm | approved spec |
| Lattice pitch | 4.235 cm, square | approved spec |
| Dimensionality | 2-D | approved spec |
| Boundary condition | reflective (all 4 lateral faces) | approved spec |

### Derived quantities (pcM's own arithmetic)

| Quantity | Value |
|---|---|
| Clad thickness | 0.051 cm |
| Fuel area | 10.3489 cm² |
| Clad area | 0.5901 cm² |
| Water area | 6.9962 cm² |
| Cell area | 17.9352 cm² |
| Fuel volume fraction | 0.57701 |
| Clad volume fraction | 0.03290 |
| Water volume fraction | 0.39009 |

Fractions sum to 1.00000.

### Assumptions (documented)

- **G1 — No fuel/clad gap.** Only two radii are given, so the clad inner
  radius equals the fuel outer radius (1.815 cm). A real TRIGA has a small
  helium gap; the spec does not include one, and pcM does not invent one.
  Impact on k: small (neutronically near-transparent), but it matters for the
  later thermal model, where a gap conductance would otherwise raise fuel
  temperature. Flagged for the thermal phase.
- **G2 — No zirconium central rod.** Physical TRIGA elements have a ~0.3 cm
  Zr rod on the axis. The spec gives a solid fuel meat from r=0 to 1.815 cm.
  pcM models what the spec says. Impact: order 100 pcm, and it changes the
  fuel volume by ~1.4 %. Recorded as a deliberate spec-faithful simplification.
- **G3 — No axial structure.** The model is 2-D, so no end fittings,
  graphite plugs, or axial reflector are represented. k-infinity only; no
  leakage.
- **G4 — Square pitch.** Specified. Note a real TRIGA Mark I uses a circular
  ring lattice; the square cell is the benchmark's idealization, not pcM's.

---

## Model 2 — Core

| Parameter | Value | Source |
|---|---|---|
| Extent | "single zone 0.495 × 0.60 m" | approved spec — **AMBIGUOUS, see below** |
| Boundary condition | vacuum | approved spec |
| Composition | single homogenized zone | approved spec (implied by "single zone") |

### ⚠ STOP-condition flag: the core dimensions are ambiguous

the project protocol lists "geometry is ambiguous" as a STOP condition. `0.495 × 0.60 m`
admits at least three readings:

| Reading | Interpretation | Consequence |
|---|---|---|
| (a) | Cylinder, **diameter** 0.495 m × height 0.60 m | R = 0.2475 m, fuel area 1924 cm² ⇒ ≈ 107 elements at 4.235 cm pitch |
| (b) | Cylinder, **radius** 0.495 m × height 0.60 m | R = 0.495 m, fuel area 7698 cm² ⇒ ≈ 429 elements — far too large for a TRIGA Mark I |
| (c) | Rectangular slab 0.495 m × 0.60 m | different leakage entirely |

**pcM's provisional interpretation: (a), cylinder of diameter 0.495 m and
height 0.60 m.** Justification: at the specified 4.235 cm pitch this yields
≈107 fuel element positions, which is the right order for a TRIGA Mark I core
(typically 60–110 elements). Reading (b) implies ~429 elements, which is not a
TRIGA Mark I. Reading (c) is possible but "zone" plus a cylindrical reactor
makes an R–H cylinder the natural form.

This interpretation is **provisional and flagged**, not silently adopted
(project protocol integrity rule 7). If the supervisor confirms a different reading,
the core model is rebuilt — it is not retro-fitted.

### Further open questions on the core model

- **G5 — Homogenization recipe undefined.** "Single zone" implies one
  homogenized material. The spec does not say how fuel/clad/water are smeared.
  pcM's default: volume-weight them using the unit-cell fractions above
  (0.57701 / 0.03290 / 0.39009), which is the self-consistent choice given the
  same spec supplies both models. Flagged because an alternative homogenization
  (e.g. including reflector or a different water fraction) changes k
  substantially.
- **G6 — No reflector specified.** Vacuum BCs directly on the core zone means
  a bare core with no graphite reflector. A physical TRIGA Mark I is
  graphite-reflected; a bare core is markedly more leaky and less reactive.
  pcM models the spec as written (bare, vacuum) and records that this is a
  large departure from the physical reactor.
- **G7 — Axial extent.** 0.60 m exceeds the TRIGA active fuel length
  (≈0.381 m). If 0.60 m is the active height, the model is taller than a real
  element; if it includes reflector/plenum, the homogenization should reflect
  that. pcM assumes 0.60 m of active homogenized core, per the spec.

---

## Coordinate and modelling conventions (pcM's own choices)

- Unit cell: x–y plane, infinite in z, origin at the pin centre.
- Core: z is the axial direction, origin at the core mid-plane.
- All dimensions carried in cm internally (OpenMC convention); the spec's
  metre values are converted once, explicitly.
