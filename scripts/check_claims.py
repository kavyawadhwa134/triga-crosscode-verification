#!/usr/bin/env python3
"""Recompute the README's headline numbers from the committed result CSVs.

Each claim is rebuilt from the data at the precision the document prints and
must appear verbatim in that document. A failure means either a result file
changed or the document's number (or wording) no longer matches the data.

Needs only the Python standard library: no OpenMC, Cardinal or nuclear data.
Run from anywhere:  python3 scripts/check_claims.py
"""

import csv
import importlib.util
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDINAL = ROOT / "results" / "cardinal"
GENFOAM = ROOT / "results" / "genfoam"
DECOMP = ROOT / "results" / "comparison" / "keff_decomposition.py"

MINUS = "−"  # the README prints a typographic minus
failures = []


def check(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"\n      {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(label)


def claim(label, doc, snippet):
    """The snippet, rebuilt from data, must appear verbatim in doc."""
    text = (ROOT / doc).read_text(encoding="utf-8")
    check(f"{label} [{doc}]", snippet in text,
          f"recomputed text not found in {doc}:\n      {snippet!r}")


def signed(x, fmt=".0f"):
    s = format(x, "+" + fmt)
    return s.replace("-", MINUS)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def one_row(path, **match):
    rows = [r for r in read_csv(path) if all(r[k] == v for k, v in match.items())]
    if len(rows) != 1:
        sys.exit(f"{path.relative_to(ROOT)}: expected one row matching {match}, found {len(rows)}")
    return rows[0]


def rho(k):
    return 1.0 - 1.0 / k


# ---------------------------------------------------------------- lattice k_inf
uc = one_row(CARDINAL / "openmc_unitcell.csv", config="production", seed="11")
k_c, s_c = float(uc["value"]), float(uc["std_dev"])

gf = one_row(GENFOAM / "validation_step5.csv", quantity="k-inf")
m = re.fullmatch(r"\s*([0-9.]+)\s*\+/-\s*([0-9.]+)\s*", gf["value"])
k_g, s_g = float(m.group(1)), float(m.group(2))

# The README's -280 pcm is the relative difference (k_C - k_G) / k_G.
diff_kinf = (k_c - k_g) / k_g * 1e5

claim("k_inf Cardinal vs GeN-Foam lattice", "README.md",
      f"k∞ = {k_c:.6f} ± {s_c * 1e5:.0f} pcm (Cardinal) vs "
      f"{k_g:.6f} ± {s_g * 1e5:.0f} pcm (GeN-Foam lattice): "
      f"**{signed(diff_kinf)} pcm**")
claim("k_inf difference (findings)", "README.md",
      f"pin cell matches to {abs(diff_kinf):.0f} pcm")
claim("k_inf regression target", "docs/reproducing.md",
      f"| k-infinity, unit cell, production | {k_c:.6f} ± {s_c:.6f} |")

# ------------------------------------------------------------------ core k_eff
core = one_row(CARDINAL / "openmc_core.csv", config="production", seed="21")
k_eff, s_eff = float(core["value"]), float(core["std_dev"])
claim("k_eff regression target", "docs/reproducing.md",
      f"| k-effective, bare core, production | {k_eff:.6f} ± {s_eff:.6f} |")

# ------------------------------------------- k_eff decomposition (script output)
# The script hard-codes its inputs; check them against the CSVs first.
spec = importlib.util.spec_from_file_location("keff_decomposition", DECOMP)
dec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dec)

homog = one_row(CARDINAL / "openmc_core_homog.csv", sab="h2o")
step5 = {(r["quantity"], r["group"]): float(r["value"])
         for r in read_csv(GENFOAM / "validation_step5.csv") if r["group"] != "-"}
step6 = one_row(GENFOAM / "validation_step6.csv", quantity="steady_keff")
inputs = [
    ("K_CARDINAL_HET", dec.K_CARDINAL_HET, k_eff, "openmc_core.csv production seed 21"),
    ("K_CARDINAL_HOMOG", dec.K_CARDINAL_HOMOG, float(homog["value"]), "openmc_core_homog.csv sab=h2o"),
    ("K_GENFOAM", dec.K_GENFOAM, float(step6["value"]), "validation_step6.csv steady_keff"),
    ("K_INF_OPENMC_LATTICE", dec.K_INF_OPENMC_LATTICE, k_g, "validation_step5.csv k-inf"),
    ("SR1", dec.SR1, step5[("removal", "fast")], "validation_step5.csv"),
    ("SR2", dec.SR2, step5[("removal", "thermal")], "validation_step5.csv"),
    ("NF1", dec.NF1, step5[("nuSigmaF", "fast")], "validation_step5.csv"),
    ("NF2", dec.NF2, step5[("nuSigmaF", "thermal")], "validation_step5.csv"),
    ("D1", dec.D1, step5[("D", "fast")], "validation_step5.csv"),
    ("D2", dec.D2, step5[("D", "thermal")], "validation_step5.csv"),
    ("S12", dec.S12, step5[("S12", "fast->thermal")], "validation_step5.csv"),
    ("S21", dec.S21, step5[("S21", "thermal->fast")], "validation_step5.csv"),
]
for name, in_script, in_csv, src in inputs:
    check(f"keff_decomposition.py {name} matches {src}", in_script == in_csv,
          f"script {in_script!r} vs CSV {in_csv!r}")

# Run a copy so the committed keff_decomposition.csv is not rewritten.
with tempfile.TemporaryDirectory() as tmp:
    script = Path(tmp) / "results" / "comparison" / DECOMP.name
    script.parent.mkdir(parents=True)
    shutil.copy(DECOMP, script)
    run = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    if run.returncode != 0:
        sys.exit(f"keff_decomposition.py failed:\n{run.stderr}")
    out = run.stdout
    regenerated = read_csv(script.parent / "keff_decomposition.csv")

check("keff_decomposition.csv matches a fresh run of the script",
      regenerated == read_csv(DECOMP.parent / "keff_decomposition.csv"),
      "committed CSV is stale; rerun results/comparison/keff_decomposition.py")


def pcm_from(pattern):
    m = re.search(pattern, out, re.MULTILINE)
    if not m:
        sys.exit(f"could not parse keff_decomposition.py output for {pattern!r}:\n{out}")
    return int(m.group(1))


step = {s: pcm_from(rf"^{s}\s+\S+ -> \S+\s+([+-]\d+) pcm")
        for s in ("homogenisation", "solution_method", "core_geometry", "discretisation")}
total = pcm_from(r"^total\s+\S+ -> \S+\s+([+-]\d+) pcm")
direct = pcm_from(r"\(direct: ([+-]\d+)\)")
extrap = pcm_from(r"extrapolated boundary instead: ([+-]\d+) pcm")

check("decomposition total equals direct difference", total == direct,
      f"sum of steps {total:+d} vs direct {direct:+d}")
check("decomposition direct difference matches CSV inputs",
      round((1 / k_eff - 1 / float(step6["value"])) * 1e5) == direct)

claim("k_eff decomposition", "README.md",
      f"The {signed(total, ',.0f').replace(',', ' ')} pcm k_eff difference decomposes exactly "
      f"(terms rounded individually): **{signed(step['core_geometry'])} pcm** from core geometry "
      f"(2-D slab vs 3-D cylinder), {signed(step['homogenisation'])} pcm from homogenisation, "
      f"{signed(step['solution_method'])} pcm from diffusion vs Monte Carlo, "
      f"{signed(step['discretisation'])} pcm discretisation")
claim("method difference, both boundaries", "README.md",
      f"**{signed(step['solution_method'])} pcm** with a zero-flux vacuum boundary, "
      f"**{signed(extrap)} pcm** with an extrapolated (Marshak) boundary")
claim("method difference range (findings)", "README.md",
      f"{signed(step['solution_method'])} to {signed(extrap)} pcm")

# ---------------------------------------------- fuel temperature coefficient
temps = {float(r["T_fuel_K"]): r for r in read_csv(CARDINAL / "core_temperature_coefficient.csv")}
lo, hi = temps[500.0], temps[600.0]
k_lo, k_hi = float(lo["k_eff"]), float(hi["k_eff"])
alpha = (rho(k_hi) - rho(k_lo)) / 100.0 * 1e5
sigma = math.hypot(float(lo["std_dev"]) / k_lo**2, float(hi["std_dev"]) / k_hi**2) / 100.0 * 1e5

claim("fuel temperature coefficient", "README.md",
      f"Fuel temperature coefficient {format(alpha, '.2f').replace('-', MINUS)} ± {sigma:.2f} pcm/K "
      f"(bare core, 500–600 K)")

# ------------------------------------------------------------ leakage feedback
bands = read_csv(CARDINAL / "leakage_feedback.csv")
b56 = next(b for b in bands if b["band_K"] == "500-600")
check("leakage_feedback.csv 500-600 K core coefficient matches core_temperature_coefficient.csv",
      f"{float(b56['alpha_keff_pcm_per_K']):.3f}" == f"{alpha:.3f}",
      f"{b56['alpha_keff_pcm_per_K']} vs recomputed {alpha:.3f}")

for b in bands:
    kinf, keff, leak = (float(b[c]) for c in
                        ("alpha_kinf_pcm_per_K", "alpha_keff_pcm_per_K", "leakage_term_pcm_per_K"))
    # columns are printed to 0.001 independently, so allow one unit of rounding
    check(f"leakage_feedback.csv {b['band_K']} K: leakage term = core - lattice",
          abs((keff - kinf) - leak) <= 0.0015, f"{keff} - {kinf} = {keff - kinf:.3f} vs {leak}")

share = [float(b["leakage_term_pcm_per_K"]) / float(b["alpha_keff_pcm_per_K"]) * 100 for b in bands]
excess = [(float(b["alpha_keff_pcm_per_K"]) / float(b["alpha_kinf_pcm_per_K"]) - 1) * 100 for b in bands]
claim("leakage share and core-vs-lattice excess", "README.md",
      f"Leakage contributes {min(share):.0f}–{max(share):.0f}% of the core coefficient, "
      f"which is {min(excess):.0f}–{max(excess):.0f}% larger in magnitude than the lattice-only value")

# ---------------------------------------------------------------------- result
print()
if failures:
    print(f"{len(failures)} check(s) failed")
    sys.exit(1)
print("all claims match the committed data")
