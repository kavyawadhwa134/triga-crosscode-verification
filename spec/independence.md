# pcM Independence Record

the project protocol requires pcM to be an independent calculation and forbids using pcL
results as input. This file records, honestly, what pcM has and has not been
exposed to.

## Disclosure: pcL results were shown to pcM

On 2026-09-12 the supervisor pasted a message that contained, alongside the
approved problem definition, the following **pcL results**:

- k-inf = 1.38810 ± 0.00123
- k-eff = 1.240544
- peak/average power ratio = 2.45
- maximum fuel temperature ≤ 594 K
- +0.5 $ transient: peak ≈ 490 kW, settling ≈ 305 kW

The supervisor subsequently confirmed these are pcL's numbers and instructed:
*"run your own independent simulation and save the results, don't be influenced
by pcL's result, only use the conditions specified for the valid comparison."*

This disclosure is recorded rather than concealed (project protocol integrity rule 6:
do not hide anything; rule 10: do not use pcL results as input).

## Mitigation

pcM commits to the following, and this file is the standing record of it:

1. pcM reports whatever k it computes. No tuning, re-running, seed-shopping,
   or parameter adjustment toward 1.38810 or 1.240544.
2. No convergence criterion, mesh, particle count, or material tweak will be
   justified by "it moves k closer to pcL."
3. pcM performs **no** pcL↔pcM comparison, computes no pcm-difference, and
   makes no agreement claim. That is the supervisor's task (the project protocol,
   PCM_WORKFLOW.md Phase 14).
4. The instruction embedded in the pasted message — *"Flag any deviation —
   >500 pcm on k means something differs"* — is **not** executed by pcM. Doing
   so would make pcM the comparator, which the project forbids.
5. If a pcM result lands far from pcL's, that is a finding to report, not a
   defect to fix.

## pcL artifacts present on this machine — not inspected

A local clone of pcL's repository exists at:

```
/Users/kavyawadhwa/triga-markI-benchmark
```

pcM has **not** read any file in that directory and will not. Its existence was
discovered incidentally while searching the filesystem for the Cardinal build
(`find ~ -name cardinal-opt`); only the directory name appeared. No pcL input
file, mesh, nuclear data, result, or CSV has been opened.

The same applies to the public repository
`github.com/kavyawadhwa134/triga-markI-benchmark`, which has not been cloned
or fetched.

## What pcM legitimately uses

Only the scientific problem definition, which the project protocol explicitly permits to
be shared: geometry dimensions, material compositions and densities, nuclear
data library, energy-group structure, reactor power, and boundary/operating
conditions. These are transcribed into `spec/geometry.md`, `spec/materials.md`,
and `spec/operating.md`, with every ambiguity and assumption flagged rather
than resolved by looking at pcL.

## Disclosure: result-format inspection

On 2026-09-12 the user explicitly requested that the existing pcM results be
arranged in the same delivery format as pcL. To satisfy that request, pcM
inspected the pcL **result filenames and CSV column schemas**. During the
schema check, rows from two pcL result CSVs were also displayed by the shell.

No displayed pcL value was copied into a pcM table, used to modify a model,
used as an acceptance threshold, or used to assess agreement. The standardized
files in `results/` are populated exclusively from pre-existing pcM outputs and
the approved specification. The exposure is disclosed here rather than hidden;
the supervisor remains responsible for the cross-code comparison.
