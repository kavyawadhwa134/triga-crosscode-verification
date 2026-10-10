# Problem specification

The shared problem definition used by **both** the Cardinal and the GeN-Foam
calculations. Only this definition was shared between the two models; each was
implemented separately. Values not given by the definition are listed as
documented assumptions, with their expected impact.

## Geometry

### Unit cell (k-infinity)

| Parameter | Value |
|---|---|
| Fuel outer radius | 1.815 cm |
| Clad outer radius | 1.866 cm |
| Lattice pitch | 4.235 cm, square |
| Dimensionality | 2-D |
| Boundary condition | reflective on all lateral faces |

The 4.235 cm square pitch preserves the cell area of the reference hexagonal
TRIGA cell, (√3/2)·4.55² = 17.93 cm².

Derived quantities:

| Quantity | Value |
|---|---|
| Clad thickness | 0.051 cm |
| Fuel / clad / water area | 10.3489 / 0.5901 / 6.9962 cm² |
| Cell area | 17.9352 cm² |
| Fuel / clad / water volume fraction | 0.57701 / 0.03290 / 0.39009 |

### Core (k-effective)

| Parameter | Value |
|---|---|
| Extent | single zone, 0.495 m × 0.60 m |
| Boundary condition | vacuum on all surfaces |

**Interpretation of the core dimensions.** "0.495 × 0.60 m" is read as a
cylinder of **diameter** 0.495 m and height 0.60 m. At the specified pitch this
gives about 107 fuel positions, the right order for a TRIGA Mark I (typically
60–110 elements). Reading 0.495 m as a radius would imply about 429 elements,
which is not a Mark I. The Cardinal heterogeneous lattice truncated by this
cylinder contains 120 fuelled positions.

### Geometry assumptions

| ID | Assumption | Impact |
|---|---|---|
| G1 | No fuel–clad gap: only two radii are given, so the clad inner radius equals the fuel radius | Neutronically negligible; a gap conductance would raise fuel temperature |
| G2 | No zirconium central rod; solid fuel meat from r = 0 | Order 100 pcm; fuel volume +1.4% |
| G3 | Unit cell is 2-D; no axial structure | k-infinity only, no axial leakage |
| G4 | Square lattice (a physical Mark I uses circular rings) | Benchmark idealisation |
| G5 | Homogenised core: volume-weighted with the unit-cell fractions above | See the homogenisation study in [`cardinal-model.md`](cardinal-model.md) |
| G6 | **Bare core, no graphite reflector**, as the vacuum boundary implies | Large: a physical TRIGA is reflected. Both models share this simplification |
| G7 | 0.60 m treated as active height (physical TRIGA fuel is about 0.38 m) | Model is taller than a real element |

## Materials

| Material | Density | Composition |
|---|---|---|
| Fuel U-ZrH₁.₆₅ | 6.0 g/cm³ | U-235 1.7, U-238 6.8, Zr 89.862, H-1 1.638 wt% (8.5 wt% U at 20% enrichment) |
| Clad SS304 | 8.00 g/cm³ *(assumed, A5)* | Fe balance, Cr 19.0, Ni 9.25, Mn 2.0, Si 1.0, C 0.08 wt% *(assumed, A6)* |
| Coolant | 1.0 g/cm³ | H₂O, unborated |

| ID | Assumption | Impact |
|---|---|---|
| A1 | Natural zirconium isotopics | Small |
| A2 | Hydrogen is H-1 only | — |
| A3 | `c_H_in_ZrH` and `c_Zr_in_ZrH` thermal scattering applied to the fuel | **Essential**: without bound-hydrogen scattering the TRIGA feedback is absent and k shifts by thousands of pcm |
| A4 | No burnable poison or erbium | — |
| A5/A6 | SS304 density and composition (not given). The two models made **different** choices: Cardinal 8.00 g/cm³ (Fe bal., Cr 19.0, Ni 9.25, Mn 2.0, Si 1.0, C 0.08 wt%); GeN-Foam lattice 7.9 g/cm³ (Fe 70.5, Cr 19.0, Ni 9.0, Mn 1.0, Si 0.5 wt%) | Tens of pcm; a small contributor to the unit-cell difference |
| A7 | Pure light water, no boron | — |
| A8 | `c_H_in_H2O` thermal scattering applied to the coolant | Required for correct thermal moderation |

**Nuclear data:** ENDF/B-VIII.0 (HDF5). The Cardinal coupled run used
ENDF/B-VII.1 because that was the library on the coupled-run platform; the
offset was measured directly (+73 pcm, see the report).

## Operating conditions

| Parameter | Value |
|---|---|
| Thermal power | 250 kW |
| Reference temperature | 293 K (all materials, cold baseline) |
| Coolant inlet | 293 K, 0.2 m/s, upward flow (assumed) |
| Pressure | 0.1 MPa, open pool (assumed) |
| Energy groups (for MGXS) | 2 groups, thermal cutoff 0.625 eV |
| Transient | +0.5 $ reactivity insertion (GeN-Foam only) |

## Acceptance criterion

A difference of **500 pcm on k** flags a material disagreement. The
comparison shows this criterion is only meaningful between methodologically
comparable quantities; see [`../results/comparison/COMPARISON.md`](../results/comparison/COMPARISON.md).
