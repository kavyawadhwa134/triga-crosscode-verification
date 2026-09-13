# LaTeX source — TRIGA Mark I cross-code report

Build with [tectonic](https://tectonic-typesetting.github.io) (self-contained, fetches
packages on demand):

```bash
tectonic -X compile report.tex --outdir .
```

Or with a standard TeX Live installation: `pdflatex report.tex` (run twice for the
table of contents).

`fig/` holds figures from both calculations:

| Prefix | Source |
|---|---|
| `pcl_*` | GeN-Foam / OFFBEAT — ParaView renders, plus the transient plotted from `transient_rod_power.csv` |
| `fig[1-7]_*` | Cardinal — regenerated from the committed CSVs by `scripts/make_report_pdf.py` |
