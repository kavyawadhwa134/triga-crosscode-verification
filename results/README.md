# pcM result package

This directory is the independent **pcM** result package prepared for the
supervisor. Its flat CSV/PNG layout mirrors the pcL delivery convention so the
supervisor can compare the two packages without renaming files.

The formatting is shared; the calculations are not. No pcL value is used in
any table, figure, input, convergence decision, or model parameter here.

## Comparison-format files

| File | Contents |
|---|---|
| `validation_step2.csv` | Internal conservation/normalization checks against the approved specification |
| `validation_step5.csv` | Independent cold OpenMC neutronics and power-distribution summary |
| `validation_step6.csv` | Binder OpenMC-MOOSE coupled-production summary |
| `validation_nekrs_gpu_diagnostic.csv` | Separate GTX 1080 Ti NekRS software/flow diagnostic; not a production or coupled result |
| `paraview_pcm_thermal_convergence.png` | OpenMC-MOOSE Picard thermal convergence |
| `paraview_pcm_neutronics_convergence.png` | Coupled k-effective and tally precision |
| `paraview_pcm_final_state_summary.png` | Final solid temperatures and power conservation |
| `paraview_pcm_solid_temperature.png` | Final fuel-and-cladding temperature field |
| `pcm_results_figures.pdf` | Combined PDF containing the four scientific figures |
| `pcm_coupled_production_vii1.csv` | Raw MOOSE postprocessor history |
| `pcm_coupled_production_openmc_vii1.csv` | Raw OpenMC sub-app history |
| `SHA256SUMS` | Integrity hashes for the standardized result package |

The original detailed pcM-native CSV files remain alongside these standardized
tables. `PCM_RESULTS.md` is the narrative scientific report.

## Scope and data labels

- Standalone cold OpenMC production results use **ENDF/B-VIII.0**.
- The Binder coupled-production result uses **ENDF/B-VII.1**.
- The coupled-production result is **OpenMC-MOOSE only**. Coolant conditions
  are imposed through the documented heat-transfer surrogate; NekRS is not in
  that coupling chain.
- The standalone NekRS GTX 1080 Ti run reached exit code 0 and demonstrates a
  working CUDA path, but its 1,000-step diagnostic was not thermally converged
  and must not be reported as the final coolant solution.
- No pcM rod-transient result exists yet, so this package intentionally does
  not fabricate a `transient_rod_power.csv` file.
- Large Exodus, OpenMC statepoint, and NekRS checkpoint files are excluded by
  the repository's Git rules. The committed CSVs and figures are the curated
  small derived results.

## Headline coupled-production values

Ten Picard iterations completed in 2,905.49 s. The final values were
`k_eff = 1.3066210577542` with OpenMC one-sigma `0.00055`, average fuel
temperature `330.390708 K`, maximum fuel temperature `358.995333 K`, average
cladding temperature `322.278940 K`, maximum cladding temperature
`336.145067 K`, and integrated pin heating `2083.33 W`.

These are independent pcM results, not a pcM-pcL comparison.
