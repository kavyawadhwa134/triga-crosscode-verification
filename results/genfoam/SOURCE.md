# GeN-Foam result provenance

These files are the GeN-Foam results exactly as produced by the GeN-Foam
calculation (inputs in [`../../genfoam/`](../../genfoam/)). They were first
committed on 10 September 2026, separately from the Cardinal model.

## Blind comparison

The Cardinal results were frozen at git tag **`pcm-independent-v1`**
(12 September 2026) before these files were read for the comparison. No
Cardinal input, setting or result was changed after reading them; the tag
makes this checkable from the history.

## Notes for interpretation

- `validation_step6.csv` describes the core as "eigenvalue diffusion, bare
  homogenized box vacuum BCs". The mesh (`genfoam/triga_steady/system/blockMeshDict`)
  shows the box is a **2-D slab**, 0.495 m × 0.60 m and one cell thick with
  `empty` front and back patches.
- `validation_step5.csv` lists `genfoam_smoke_keff = 1.331`. This is a
  diffusion solution on a separate 2-D channel test geometry, not on the pin
  cell, so it is not a direct method benchmark.
