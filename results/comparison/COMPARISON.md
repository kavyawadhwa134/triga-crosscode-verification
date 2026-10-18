# Cardinal ↔ GeN-Foam comparison — TRIGA Mark I

| | |
|---|---|
| Cardinal | OpenMC continuous-energy Monte Carlo + MOOSE conduction + NekRS (diagnostic) |
| GeN-Foam | 2-group diffusion + porous-medium thermal-hydraulics + sub-scale fuel pin |
| Protocol | Cardinal results frozen at git tag `pcm-independent-v1` before any GeN-Foam input, mesh or output file was read. GeN-Foam's headline values were stated in the task brief; no Cardinal parameter was adjusted toward them |
| Criterion | 500 pcm on k flags a material difference |

Machine-readable table: [`crosscode_comparison.csv`](crosscode_comparison.csv).
Full discussion: [`../../docs/TRIGA_MarkI_CrossCode_Report.pdf`](../../docs/TRIGA_MarkI_CrossCode_Report.pdf).

## 1. Summary

| # | Quantity | Cardinal | GeN-Foam | Difference | Comparable? |
|---|---|---|---|---|---|
| 1 | k∞, unit cell (Monte Carlo both) | 1.384207 ± 21 pcm | 1.388100 ± 123 pcm | **−280 pcm** (3.1σ) | ✅ within criterion |
| 2 | k_eff, as modelled | 1.102059 ± 26 pcm | 1.240544 | Δρ = +10 129 pcm | ❌ different geometry |
| 3 | k_eff, same homogenised cylinder | 1.145259 ± 74 pcm (MC) | 1.140929 (2-group diffusion, analytic) | **Δρ = −331 pcm** | ✅ within criterion |
| 4 | Group constants, k∞ | — | 1.38873 vs own OpenMC 1.38810 | +33 pcm | GeN-Foam internal |
| 5 | Fuel temperature coefficient, 500–600 K (core) | −10.79 ± 0.82 pcm/K | −10.0 pcm/K (published constant) | **+7%** (within 1σ) | ✅ |
| 6 | Power peaking | 2.2544 | 2.45 | −8% | ❌ different geometry |
| 7 | Max fuel temperature | 359.0 K (average pin) | 594.2 K (sub-scale pin) | — | ❌ different pin basis |
| 8 | Max coolant temperature | diagnostic only | 306.5 K | — | ❌ |
| 9 | Total power | 250 kW | 250 kW | 0 | ✅ by specification |
| 10 | +0.5 $ transient | not run | 489.7 kW peak | — | ❌ |

## 2. Lattice: the like-for-like comparison

Both sides solved the same 2-D reflective pin cell with OpenMC and
ENDF/B-VIII.0. They differ by **−280 pcm at 3.1σ**: statistically resolved,
inside the 500 pcm criterion. Part of the residual is a documented input
difference (SS304 cladding at 8.00 vs 7.9 g/cm³ with different trace
elements).

## 3. Core eigenvalue: mostly geometry

The specification gives the core as "single zone 0.495 × 0.60 m" without a
shape. Cardinal modelled a 3-D cylinder of diameter 49.5 cm; GeN-Foam modelled
a 2-D slab 49.5 cm wide and 60 cm tall, infinite in the third direction. The
slab's geometric buckling is 56% of the cylinder's, so it leaks far less.

[`keff_decomposition.py`](keff_decomposition.py) solves GeN-Foam's own
two-group constants analytically in both geometries and splits the difference
into additive reactivity steps (ρ = 1 − 1/k):

| Step | k: from → to | Δρ (pcm) |
|---|---|---|
| Homogenisation (Monte Carlo both sides) | 1.10206 → 1.14526 | +3423 |
| Solution method (same cylinder, MC → diffusion) | 1.14526 → 1.14093 | −331 |
| Core geometry (diffusion, cylinder → slab) | 1.14093 → 1.24030 | +7022 |
| Discretisation (analytic → GeN-Foam) | 1.24030 → 1.24054 | +16 |
| **Total** | 1.10206 → 1.24054 | **+10 129** |

![k-effective decomposition](../../docs/report/fig/fig6_keff.png)

- **GeN-Foam's solver is verified:** it reproduces the analytic solution of its
  own geometry to 16 pcm.
- **Geometry interpretation is about 70% of the difference.**
- **With geometry matched, diffusion and Monte Carlo agree to 331 pcm**
  (1468 pcm with an extrapolated rather than zero-flux vacuum boundary). Both
  lie within the 1275 pcm spread of the homogenised Monte Carlo result across
  hydrogen scattering kernels.
- The +3423 pcm homogenisation step is the classical two-step error: smearing
  removes resonance self-shielding and forces one hydrogen kernel on hydrogen
  that is 56% ZrH-bound and 44% water-bound.

> **Correction.** An earlier version of this comparison attributed +8320 pcm to
> diffusion-versus-Monte-Carlo error, assumed both cores were the same bare box,
> and used GeN-Foam's `genfoam_smoke_keff = 1.331` as a pin-cell method
> benchmark. The GeN-Foam mesh is a 2-D slab and the smoke test used a separate
> channel geometry; the decomposition above replaces that analysis.

## 4. Fuel temperature coefficient

| | 500–600 K | vs GeN-Foam |
|---|---|---|
| Cardinal k∞ (unit cell, no leakage) | −7.76 ± 0.47 pcm/K | −29% |
| **Cardinal k_eff (bare core, 20.1% leakage)** | **−10.79 ± 0.82 pcm/K** | **+7%** |
| GeN-Foam input (`feedbackCoeffTFuel`) | −10.0 pcm/K | — |

A transient follows the core eigenvalue, so the k_eff coefficient is the right
basis: the published constant used by GeN-Foam agrees with Cardinal's computed
value within one standard deviation. Two caveats: the computed coefficient
varies from −6.3 to −10.8 pcm/K over 296–1000 K, so a constant is only adequate
near 500–600 K; and GeN-Foam's slab leaks less than the cylinder, so the
coefficient for its own geometry would sit between the lattice and core values.

## 5. Not comparable as reported

- **Fuel temperatures:** Cardinal is an average pin with a correlation film
  coefficient; GeN-Foam is a sub-scale pin in a porous-medium core.
- **Coolant temperatures:** the Cardinal NekRS run is a diagnostic only
  (incomplete heated-wall tagging, 34.6% energy closure).
- **Transient:** computed by GeN-Foam only, so it has no independent check.

## 6. Recommended next steps

1. Re-run GeN-Foam on the specified 3-D cylinder to confirm the geometry term
   numerically.
2. Replace the constant feedback coefficient with Cardinal's
   temperature-dependent values and re-run the transient.
3. Regenerate the NekRS mesh and rerun the coolant CFD to convergence.
4. Add a reflector and control rods to both models.
