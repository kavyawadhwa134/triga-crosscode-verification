# pcM Thermal Properties and Correlations

**These are pcM assumptions, not approved specification values.**

The approved problem definition (`spec/materials.md`, `spec/operating.md`)
gives compositions, densities, power, temperature and coolant velocity, but
**no thermal transport properties and no heat transfer coefficient**. The
MOOSE conduction model and the NekRS fluid model cannot be built without them.

Per the project protocol, each assumption below records what it is, why it is needed, its
source, and its expected impact. None of these values came from pcL.

---

## T1 — Fuel thermal conductivity

| | |
|---|---|
| **Value** | `k_fuel` = 18 W/m·K = **0.18 W/cm·K** |
| **Why needed** | `HeatConduction` in `cardinal/coupling/solid.i` requires a conductivity for blocks `fuel` and `fuel_center`. |
| **Source** | Published U-ZrH₁.₆₅ TRIGA fuel data. Hydride fuel conductivity is roughly constant at 17–20 W/m·K over 300–1000 K and is only weakly temperature-dependent. |
| **Impact** | Sets the fuel centreline-to-surface temperature drop, `ΔT = q′/(4πk)`. At the peak linear power of 54.5 W/cm this contributes **24.1 K**, about 37% of the total rise above coolant. A ±10% error in `k_fuel` moves peak fuel temperature by ≈ ±2.4 K. |
| **Note** | Treated as constant. A temperature-dependent `k(T)` would be a refinement; the weak dependence of hydride fuel makes this second-order here. This is **much** higher than UO₂ (~3 W/m·K) — using an LWR value would be badly wrong. |

## T2 — Clad thermal conductivity

| | |
|---|---|
| **Value** | `k_clad` = 16 W/m·K = **0.16 W/cm·K** |
| **Why needed** | Conductivity for the `clad` block. |
| **Source** | Standard SS304 value near 300–400 K. |
| **Impact** | `ΔT = q′/(2πk)·ln(r_o/r_i)`. With the 0.051 cm clad this is only **1.5 K**, ~2% of the total rise. Even a 50% error shifts peak fuel temperature by <1 K, so this is the least sensitive of the four. |

## T3 — Convective heat transfer coefficient

| | |
|---|---|
| **Value** | `h` = 1098 W/m²·K = **0.109778 W/cm²·K** |
| **Why needed** | `ConvectiveFluxFunction` boundary condition on the clad outer surface (`rmax`) closes the conduction problem. **Placeholder until NekRS supplies the real wall heat transfer.** |
| **Source** | Dittus–Boelter, `Nu = 0.023 Re^0.8 Pr^0.4` (heating), evaluated by pcM from spec quantities. |

Derivation, from spec geometry and operating conditions, water at 293 K
(ρ = 998 kg/m³, μ = 1.002×10⁻³ Pa·s, k = 0.598 W/m·K, c_p = 4182 J/kg·K):

```
A_flow = pitch² − π·r_clad²  = 4.235² − π·1.866²  = 6.9963 cm²
P_wet  = 2π·r_clad           = 11.725 cm
D_h    = 4·A_flow/P_wet      = 2.3869 cm
Re     = ρ·v·D_h/μ           = 4755
Pr     = μ·c_p/k             = 7.01
Nu     = 0.023·Re^0.8·Pr^0.4 = 43.82
h      = Nu·k/D_h            = 1098 W/m²·K
```

| | |
|---|---|
| **Impact** | **Dominant.** The film drop `q′/(2π·r_o·h)` is **42.4 K**, about 65% of the total rise above coolant. Peak fuel temperature is more sensitive to this one correlation than to everything else combined; a ±20% error moves it by ≈ ∓7 K. |
| **Caveats** | Re = 4755 is **transitional**, where Dittus–Boelter (strictly for fully turbulent, Re > 10⁴) is least reliable. It is also a circular-tube correlation applied to a rod-in-square-channel subchannel. Both push the uncertainty well above the ±20% typical of the correlation in its proper range. **This is the weakest link in the current thermal result and the main reason to run NekRS.** |

## T4 — Coolant bulk temperature rise

| | |
|---|---|
| **Value** | **3.567 K** over the 60 cm channel, applied as a linear axial profile |
| **Why needed** | `T_infinity` for the convective boundary condition. Placeholder until NekRS computes the real coolant field. |
| **Source** | pcM energy balance at the specified 0.2 m/s and 2083.33 W per pin. |

```
ṁ  = ρ·v·A_flow = 998 × 0.2 × 6.9963e-4 = 0.13965 kg/s
ΔT = Q/(ṁ·c_p)  = 2083.33/(0.13965 × 4182) = 3.567 K
```

| | |
|---|---|
| **Impact** | Small and well-constrained — it follows directly from conservation of energy, so it is the most trustworthy of the four. It shifts the whole temperature profile by ≈ 1.8 K at mid-plane. |
| **Assumed** | Linear axial rise. The true profile follows the integrated axial power shape and is mildly S-shaped; the difference is a fraction of a kelvin. |

## T5 — Per-pin power

| | |
|---|---|
| **Value** | **2083.33 W** per pin |
| **Why needed** | Normalization for the coupled OpenMC/MOOSE model. |
| **Source** | pcM's own core calculation: 250 kW ÷ 120 fuelled pins. Derived from pcM results only. |
| **Impact** | Scales every temperature difference linearly. This is the **average** pin; pcM's own bare-core result gives a pin peak/average of 2.2544, so a hot-pin analysis would raise the linear power and all temperature drops by that factor. The coupled result reported so far is therefore an **average-pin** result, not a hot-channel one. |

---

## Sensitivity summary

At peak linear power 54.5 W/cm, the rise above local coolant temperature:

| Contribution | ΔT (K) | Share | Governed by |
|---|---|---|---|
| Film (clad → coolant) | 42.4 | 65% | **T3 — weakest** |
| Fuel conduction | 24.1 | 37% | T1 |
| Clad conduction | 1.5 | 2% | T2 |

Total predicted peak ≈ 362.8 K analytically vs 358.8 K from the coupled
Cardinal solve — **1.1% agreement**, the residual explained by the true axial
power shape being flatter than the cosine assumed in the hand calculation.

## Verification status

These values support a **physics-verified** conduction solution (conservation
holds exactly; the profile matches an independent analytic solution). They are
**not** experimentally validated, and T3 in particular is an engineering
correlation used outside its nominal range. Replacing T3 and T4 with a NekRS
solution is the single highest-value remaining improvement to the thermal
result.
