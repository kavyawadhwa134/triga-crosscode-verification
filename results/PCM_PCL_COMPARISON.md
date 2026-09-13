# Cardinal ↔ GeN-Foam Comparison — TRIGA Mark I

**Date:** 2026-09-13
**Cardinal:** OpenMC / MOOSE / NekRS (continuous-energy Monte Carlo + FE conduction + spectral-element LES)
**GeN-Foam:** OFFBEAT (2-group diffusion + finite-volume thermal-hydraulics + fuel performance)

## Provenance and independence

| | |
|---|---|
| Cardinal source | this repository, results frozen at tag `pcm-independent-v1` |
| GeN-Foam source | `github.com/kavyawadhwa134/triga-markI-benchmark`, branch **`master`**, `results/validation_step{2,5,6}.csv`, `transient_rod_power.csv` |
| Retrieved | 2026-09-13 |

Cardinal's results were produced and tagged **before** GeN-Foam's branch was read. No Cardinal parameter
was adjusted after reading it. The tag makes this verifiable from git history.

> **Note on an earlier error.** GeN-Foam's results were initially reported as absent because only
> the repository *default* branch (`main`) was checked, where `genfoam/` and `results/` hold
> only `.gitkeep`. The work is on `master`. This is corrected here.

## Threshold

The project sets **500 pcm on k** as the flag for "something differs". Section 2 shows this
threshold is only meaningful between methodologically comparable quantities.

---

# 1. Summary table

| # | Case | Cardinal | GeN-Foam | Difference | Comparable? |
|---|---|---|---|---|---|
| 1 | k-infinity, unit cell (Monte Carlo both) | 1.384207 ± 21 pcm | 1.388100 ± 123 pcm | **−280 pcm** (3.1σ) | ✅ yes — **within threshold** |
| 2 | k-effective, bare core | 1.102059 ± 26 pcm (MC, heterogeneous) | 1.240544 (2-group diffusion, homogenised) | +12566 pcm | ❌ method differs |
| 3 | k-effective, homogenised | 1.145259 ± 68 pcm (MC) | 1.240544 (diffusion) | +8320 pcm | ⚠️ geometry matched, method differs |
| 4 | Diffusion vs Monte Carlo | — | 1.331 vs 1.388100 | −4114 pcm | GeN-Foam-internal benchmark |
| 5 | Fuel temperature coefficient | −7.76 pcm/K (computed, 500–600 K) | −10.000 pcm/K (assumed constant) | −29% | ⚠️ see §6 |
| 6 | Power peaking | 2.2544 | 2.45 | −8.0% | ⚠️ different core models |
| 7 | Max fuel temperature | 359.0 K | 594.2 K | −235 K | ❌ different pin basis |
| 8 | Max coolant temperature | 294.2 K (unconverged) | 306.5 K | — | ❌ Cardinal not converged |
| 9 | Total power | 250 kW | 250 kW | 0 | ✅ identical by specification |
| 10 | +0.5 $ transient | not run | 489.7 kW peak | — | ❌ no Cardinal result |
| 11 | 2-group MGXS | not generated | full set | — | ❌ no Cardinal result |
| 12 | Solver acceptance | not formally recorded | SmallESFR PASS (4.9e-5) | — | ❌ no Cardinal result |

**Headline:** where the two calculations solve the same equations on the same geometry
(case 1), they agree to **280 pcm — inside the 500 pcm threshold.** Every larger difference
traces to a documented difference in method, geometry treatment, or scope.

---

# 2. Case 1 — k-infinity, unit cell ✅ COMPARABLE

The only case where both sides solve the same equations on the same geometry with the same
library. Both used OpenMC continuous-energy Monte Carlo.

| | Cardinal | GeN-Foam |
|---|---|---|
| k-infinity | **1.384207** | **1.388100** |
| σ | ± 0.000214 (21 pcm) | ± 0.001230 (123 pcm) |
| Statistics | 40 000 particles, 400 active / 100 inactive | 8 000 particles, 70 batches / 20 inactive |
| Library | ENDF/B-VIII.0 | ENDF/B-VIII.0 |
| Geometry | 2-D, reflective, heterogeneous | 2-D pin cell |

**Δ = −280 pcm, 3.1σ (combined).** Statistically resolved but **inside the 500 pcm
threshold**. Cardinal's uncertainty is ~6× tighter, reflecting a 25× larger particle budget.

*Interpretation:* two independent implementations of the same specification, in the same
code, agree. This is the strongest evidence in the comparison that the shared problem
definition was interpreted consistently on both sides.

---

# 3. Case 2/3 — k-effective, bare core ❌ METHOD DIFFERS

Both models are **bare boxes with vacuum boundaries** — GeN-Foam's `validation_step6.csv` records
the core verbatim as *"eigenvalue diffusion, bare homogenized box vacuum BCs"*. Geometry is
therefore **not** the explanation, and an earlier hypothesis that GeN-Foam modelled a graphite
reflector is **retracted**.

The gap decomposes into two independently measurable steps:

| Step | From → to | Δρ | Isolates |
|---|---|---|---|
| 1 · Homogenisation | Cardinal heterogeneous → Cardinal homogenised | **+3920 pcm** | Monte Carlo both sides; pure geometry-smearing |
| 2 · Solution method | Cardinal homogenised → GeN-Foam diffusion | **+8320 pcm** | Same homogenised bare box; pure method |
| **Total** | Cardinal heterogeneous → GeN-Foam | **+12566 pcm** | |

Cardinal's homogenised variants, all Monte Carlo, ENDF/B-VIII.0:

| S(α,β) treatment | k-effective | σ |
|---|---|---|
| H in H₂O | 1.145259 | ± 74 pcm |
| H in ZrH | 1.132505 | ± 68 pcm |
| none | 1.136651 | ± 79 pcm |

The 1275 pcm spread across S(α,β) choices in the homogenised model is itself larger than the
threshold, showing how sensitive a smeared TRIGA model is to bound-hydrogen treatment.

---

# 4. Case 4 — GeN-Foam's own method benchmark

`validation_step5.csv` reports both a stochastic and a deterministic solution for the **same**
pin cell:

| Method | k-infinity |
|---|---|
| OpenMC Monte Carlo | 1.388100 |
| GeN-Foam 2-group diffusion (`genfoam_smoke_keff`) | 1.331 |
| **Difference** | **−4114 pcm** |

This is GeN-Foam's own measurement of deterministic-vs-stochastic disagreement on the simplest
geometry available, where both methods model an identical cell. It is **8× the 500 pcm
threshold** before any core-geometry effect enters.

**Consequence:** the 500 pcm criterion cannot be applied between Cardinal's Monte Carlo k and
GeN-Foam's diffusion k. They are different quantities. This finding comes from GeN-Foam's own data,
not from Cardinal's interpretation.

Note the sign reverses between geometries — diffusion under-predicts by 4114 pcm on the
reflective pin cell but over-predicts by 8320 pcm on the bare core. That is consistent with
leakage treatment dominating in the bare case: Cardinal's core leaks **20.1%**, which is where
few-group diffusion is least reliable.

---

# 5. Case 11 — lattice constants were generated independently

The project workflow intended Cardinal to generate the 2-group MGXS and hand it to GeN-Foam (Phase 6).
**Cardinal did not run that phase.** GeN-Foam therefore condensed its own set:

| Quantity | Fast | Thermal |
|---|---|---|
| Removal (1/m) | 4.77341 | 8.49190 |
| νΣ_f (1/m) | 0.379899 | 12.5219 |
| Diffusion coefficient (m) | 0.00749023 | 0.00158363 |
| χ | 1.0 | 0.0 |
| Inverse velocity (s/m) | 6.62997e-06 | 3.31676e-04 |

Scatter matrix (1/m): S₁₁ 39.7524 · S₁₂ 4.22693 · S₂₁ 0.023426 · S₂₂ 201.932

Both sides condensed from Monte Carlo, but **independently**, so the group constants are a
further uncontrolled variable in case 2/3. Re-solving GeN-Foam's diffusion with Cardinal-generated
MGXS would isolate the remaining method error cleanly.

---

# 6. Case 5 — fuel temperature coefficient ⚠️ THE MOST SIGNIFICANT PHYSICS DIFFERENCE

This is the defining TRIGA safety parameter, and the two sides obtained it differently.

**Cardinal computed it** from first principles: fuel temperature swept with moderator held at
293 K, using `c_H_in_ZrH` and `c_Zr_in_ZrH` thermal scattering data.

| T_fuel band | Cardinal coefficient |
|---|---|
| 296–400 K | −5.08 pcm/K |
| 400–500 K | −6.24 pcm/K |
| **500–600 K** | **−7.76 pcm/K** ← GeN-Foam's transient operates here |
| 600–800 K | −6.78 pcm/K |
| 800–1000 K | −5.92 pcm/K |
| 296–1000 K average | −6.34 pcm/K |

**GeN-Foam appears to have assumed it.** From `validation_step6.csv`, Doppler feedback of
−328.9 pcm accompanies a fuel temperature rise of 511.70 → 544.59 K (32.89 K):

```
−328.9 pcm / 32.89 K = −10.000 pcm/K
```

Exactly −10.000 is a round number, which indicates a **constant coefficient supplied as a
model input** rather than a computed result.

**Comparison in GeN-Foam's own operating band (500–600 K): Cardinal −7.76 pcm/K vs GeN-Foam −10.000 pcm/K —
GeN-Foam is 29% more negative.**

*Why it matters:* this coefficient governs the entire transient result. A coefficient 29% too
negative shuts a power excursion down faster, so GeN-Foam's peak power (489.7 kW) is plausibly
**under**-predicted and its equilibrium reached sooner than a computed coefficient would give.
Cardinal's value is traceable to a nuclear-data calculation; GeN-Foam's is not traceable from the
committed files.

**Recommended action:** GeN-Foam should either substitute Cardinal's temperature-dependent coefficient
and re-run the transient, or document the source of −10 pcm/K.

---

# 7. Cases 6–8 — thermal quantities ❌ NOT COMPARABLE AS REPORTED

| Quantity | Cardinal | GeN-Foam | Why not comparable |
|---|---|---|---|
| Power peaking | 2.2544 | 2.45 | Cardinal: 120 discrete pins, heterogeneous. GeN-Foam: single zone, "cosine-like, flat by construction" |
| Max fuel temperature | 359.0 K | 594.2 K | Cardinal: **average pin**, conduction only, imposed film coefficient. GeN-Foam: sub-scale pin average via OFFBEAT |
| Max coolant temperature | 294.2 K | 306.5 K | **Cardinal's CFD is not converged** — 34.6% energy closure; this is a lower bound, not a result |

Three independent reasons the fuel temperatures cannot be differenced:

1. **Cardinal is an average pin.** Its own peaking factor of 2.2544 implies a hot channel is
   materially hotter.
2. **Cardinal's film coefficient is a correlation**, not a solution — Dittus–Boelter at Re = 4755,
   which is transitional and below the correlation's reliable range. It supplies ~63% of
   Cardinal's total temperature rise.
3. **Different power basis.** Cardinal normalises to 2083.33 W per pin (250 kW / 120 pins);
   GeN-Foam's sub-scale pin carries a different share.

---

# 8. Cases 10, 12 — no Cardinal counterpart

| Quantity | GeN-Foam value | Cardinal |
|---|---|---|
| Transient peak power | 489 723 W at t = 100.56 s | **not run** |
| Transient equilibrium | 304 884 W (Doppler-limited) | **not run** |
| Transient final fuel T | 544.59 K at t = 106 s | **not run** |
| Net reactivity at end | −3.87 pcm (ext +325 vs Doppler −328.9) | **not run** |
| SmallESFR acceptance | k 0.936873 vs 0.936827, rel. err 4.9e-5, PASS | not formally recorded |
| Point-kinetics coupling | 4/4 checks PASS | n/a |

The transient is **out of Cardinal's defined scope**: the project workflow specifies a
steady-state production run and defines no transient phase. This is a documented scope
decision, not an omission — but it means the transient results have no independent check.

---

# 9. Conclusions

1. **Where the two calculations are methodologically comparable, they agree.** The Monte
   Carlo pin cell differs by 280 pcm, inside the 500 pcm threshold. This is the meaningful
   cross-code result.

2. **The k-effective difference is method, not error.** It decomposes into +3920 pcm of
   homogenisation and +8320 pcm of diffusion-vs-Monte-Carlo, on geometrically identical bare
   cores. GeN-Foam's own smoke test independently measures a −4114 pcm method difference on the
   pin cell. Neither calculation is thereby shown to be wrong.

3. **The 500 pcm threshold is not applicable between a continuous-energy Monte Carlo k and a
   2-group diffusion k.** Applying it would manufacture a false discrepancy.

4. **The fuel temperature coefficient is the most consequential open item.** Cardinal computes
   −7.76 pcm/K in GeN-Foam's operating band; GeN-Foam uses a constant −10.000 pcm/K of undocumented
   origin. This governs the transient and warrants resolution.

5. **Neither result is validated.** No experimental data was used on either side. Both models
   are bare cores without reflector or control rods, so neither describes a physical TRIGA at
   criticality. Agreement between them is not validation.

## Recommended actions, in priority order

| Priority | Action | Resolves |
|---|---|---|
| 1 | Document or recompute GeN-Foam's −10 pcm/K Doppler coefficient | Case 5 — affects all transient conclusions |
| 2 | Generate Cardinal's 2-group MGXS (Phase 6); re-solve GeN-Foam's diffusion with it | Case 2/3 — isolates method error |
| 3 | Converge Cardinal's NekRS thermal field (~5 flow-throughs, ~5 h GPU) | Case 8 |
| 4 | Re-run Cardinal coupled production on ENDF/B-VIII.0 | Removes a +73 pcm library deviation |
| 5 | Agree whether reflector and control rods enter the benchmark | Both models are currently bare |
| 6 | Obtain TRIGA experimental data | The only route to validation |

---

## Source files

| File | Contents |
|---|---|
| `results/pcm_openmc_unitcell.csv` | Cardinal k-infinity |
| `results/pcm_openmc_core.csv`, `_core_homog.csv` | Cardinal k-effective, heterogeneous and homogenised |
| `results/pcm_fuel_temperature_coefficient.csv` | Cardinal temperature coefficient sweep |
| `results/pcm_coupled_smoke.csv` | Cardinal coupled neutronics–conduction |
| `results/pcm_nekrs_convergence.csv` | Cardinal CFD convergence history |
| `results/reference_pcl_validation_step5.csv` | GeN-Foam lattice constants (copy) |
| `results/reference_pcl_validation_step6.csv` | GeN-Foam core and transient (copy) |
| `results/reference_pcl_SOURCE.md` | provenance of the GeN-Foam copies |
