#!/usr/bin/env python3
"""Waterfall chart of the core k-effective decomposition (keff_decomposition.csv)."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
rows = list(csv.DictReader(open(HERE / "keff_decomposition.csv")))
labels = ["Homogenisation\n(MC → MC)", "Solution method\n(MC → diffusion,\nsame cylinder)",
          "Core geometry\n(3-D cylinder →\n2-D slab)", "Discretisation\n(analytic →\nGeN-Foam)"]
vals = [float(r["delta_rho_pcm"]) for r in rows]

BLUE, ORANGE, GREEN, INK, INK2, GRID = "#2A78D6", "#E8693A", "#1AA874", "#14171C", "#565C66", "#E3E6EB"
fig, ax = plt.subplots(figsize=(8.6, 4.2), dpi=200)
cum = 0.0
for i, v in enumerate(vals):
    color = ORANGE if v >= 0 else BLUE
    ax.bar(i, v, bottom=cum, color=color, width=0.62, zorder=3)
    ax.text(i, cum + v + (180 if v >= 0 else -180), f"{v:+,.0f}", ha="center",
            va="bottom" if v >= 0 else "top", fontsize=9, color=INK)
    if i < len(vals) - 1:
        ax.plot([i + 0.31, i + 0.69], [cum + v, cum + v], color=INK2, lw=0.8, zorder=2)
    cum += v
total = (1 / float(rows[0]["k_from"]) - 1 / float(rows[-1]["k_to"])) * 1e5
ax.bar(len(vals), total, color=GREEN, width=0.62, zorder=3)
ax.text(len(vals), total + 180, f"{total:+,.0f}", ha="center", va="bottom", fontsize=9, color=INK)
ax.axhline(0, color=INK2, lw=0.8)
ax.set_xticks(range(len(vals) + 1), labels + ["Total\nCardinal → GeN-Foam"], fontsize=8, color=INK2)
ax.set_ylabel("Reactivity change Δρ (pcm)", fontsize=9, color=INK)
ax.set_ylim(-1200, cum + 1500)
ax.tick_params(axis="y", labelsize=8, colors=INK2)
ax.grid(axis="y", color=GRID, zorder=0)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK2)
fig.tight_layout()
out = ROOT / "docs" / "report" / "fig" / "fig6_keff.png"
fig.savefig(out)
print(f"wrote {out.relative_to(ROOT)}")
