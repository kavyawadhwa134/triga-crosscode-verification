# pcL reference data — provenance

These two files are **pcL's results, not pcM's**. They are copied here solely so the
comparison in `docs/pcm_report.html` is reproducible.

- Source: `github.com/kavyawadhwa134/triga-markI-benchmark`, branch **`master`**
  (note: the repository default branch is `main`, where these directories are empty)
- Retrieved: 2026-09-13
- Files: `results/validation_step5.csv`, `results/validation_step6.csv`

## Independence

pcM's own results were frozen at git tag **`pcm-independent-v1`** before this branch was
read. Nothing in pcM's model, inputs or results derives from these files, and no pcM
parameter was adjusted after reading them.

## Key metadata that resolved the k-effective question

`validation_step6.csv` records pcL's core as:

> `eigenvalue diffusion, bare homogenized box vacuum BCs`

Both calculations are therefore bare with vacuum boundaries, which eliminates a reflector
difference as the explanation and attributes the gap to homogenisation plus solution method.

`validation_step5.csv` additionally reports `genfoam_smoke_keff = 1.331` against pcL's own
OpenMC pin-cell k-infinity of 1.38810 — a −4114 pcm deterministic-vs-stochastic difference
measured by pcL on a geometry where both methods model the identical cell.
