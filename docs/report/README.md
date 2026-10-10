# Report source

LaTeX source for [`../TRIGA_MarkI_CrossCode_Report.pdf`](../TRIGA_MarkI_CrossCode_Report.pdf).
Build with [tectonic](https://tectonic-typesetting.github.io):

```bash
tectonic -X compile report.tex --outdir ..
mv ../report.pdf ../TRIGA_MarkI_CrossCode_Report.pdf
```

or with TeX Live: `pdflatex report.tex` (run twice for the table of contents).

| Figure | Source |
|---|---|
| `genfoam_*` | GeN-Foam ParaView renders and the transient plotted from `results/genfoam/transient_rod_power.csv` |
| `fig1`–`fig5`, `fig7`, `fig8` | Cardinal results, plotted from the CSVs in `results/cardinal/` |
| `fig6_keff.png` | `results/comparison/plot_keff_decomposition.py` |
| `cardinal_solid_temperature.png` | Final coupled fuel and clad temperature field (Exodus output) |
