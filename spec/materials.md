# pcM Materials Specification

Source: approved problem definition supplied by the supervisor 2026-09-12.
Implementation is pcM's own (project protocol: only the problem definition is shared).

## M1 — Fuel: U-ZrH(1.65)

| Property | Value | Source |
|---|---|---|
| Density | 6.0 g/cm³ | approved spec |
| U-235 | 1.7 wt% | approved spec |
| U-238 | 6.8 wt% | approved spec |
| Zr | 89.862 wt% | approved spec |
| H-1 | 1.638 wt% | approved spec |

Weight fractions sum to 100.000 %. Total uranium 8.5 wt%, enrichment
1.7/8.5 = 20.0 % U-235 — consistent with TRIGA LEU fuel.

**Assumptions (pcM, documented):**

- **A1** Zr is natural isotopic composition (Zr-90/91/92/94/96). The spec says
  "Zr" without isotopics. Impact: small; natural Zr is the physical material.
- **A2** H is specified as H-1 explicitly, so no deuterium is modelled.
- **A3** Thermal scattering law `c_H_in_ZrH` and `c_Zr_in_ZrH` (S(α,β)) are
  applied to the fuel. This is **essential physics** for a hydride-moderated
  TRIGA — omitting it would shift k by several thousand pcm. The spec does not
  mention S(α,β); pcM applies it because free-gas H in ZrH is physically wrong.
  Flagged for supervisor confirmation, as it is a consequential choice.
- **A4** No burnable poison, no erbium, no carbon. The spec lists exactly four
  constituents summing to 100 %, so none is added.

## M2 — Clad: SS304

| Property | Value | Source |
|---|---|---|
| Density | 8.00 g/cm³ | **pcM assumption (A5)** — not in spec |
| Composition | standard SS304 | **pcM assumption (A6)** — not in spec |

**Assumption A5/A6:** the spec names "SS304" but gives neither density nor
composition. pcM uses the conventional SS304 definition:

| Element | wt% |
|---|---|
| Fe | balance (~68.7) |
| Cr | 19.0 |
| Ni | 9.25 |
| Mn | 2.0 |
| Si | 1.0 |
| C | 0.08 |

Impact: clad is a thin (0.051 cm) absorber; a ±5 % density error or minor
composition variation is a small but non-zero reactivity effect (order tens of
pcm). Recorded so the supervisor can supply the approved values if they differ.

## M3 — Coolant/Moderator: Light water

| Property | Value | Source |
|---|---|---|
| Density | 1.0 g/cm³ | approved spec |
| Composition | H₂O, natural H and O | approved spec (implied) |

**Assumptions:**

- **A7** Pure light water. No boron, no impurities — the spec states only
  "water ρ 1.0".
- **A8** Thermal scattering law `c_H_in_H2O` applied. Same reasoning as A3:
  free-gas hydrogen in water is physically wrong at thermal energies.

## Nuclear data

| Item | Value |
|---|---|
| Library | ENDF/B-VIII.0 |
| Format | HDF5 |
| Path | `/Users/kavyawadhwa/Documents/Digital Twin/nuclear_data/endfb-viii.0-hdf5/cross_sections.xml` |

Matches the approved specification. Checksum to be recorded before production.

## Temperature for cross-section evaluation

All materials at **293 K** for the baseline (see `spec/operating.md`). Fuel
temperature becomes a coupled field in later phases; the standalone OpenMC
baseline is the cold, clean state.

## Open items for supervisor

1. SS304 density and composition — confirm or supply approved values (A5/A6).
2. Confirm S(α,β) treatment is intended (A3/A8). pcM considers it physically
   required; noting it because it materially affects k.
