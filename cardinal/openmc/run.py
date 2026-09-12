"""pcM OpenMC driver.

Usage:
    python run.py unitcell smoke
    python run.py unitcell baseline [--seed N]
    python run.py core baseline

Writes a compact CSV with k_eff, uncertainty, and full reproduction metadata.
"""

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import openmc

sys.path.insert(0, str(Path(__file__).parent))

import geometry as geo
import materials as mat
import settings as st
import tallies as tal

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
CONFIGS = {"smoke": st.SMOKE, "baseline": st.BASELINE, "production": st.PRODUCTION}


def library_checksum():
    xs = os.environ.get("OPENMC_CROSS_SECTIONS", "")
    if not xs or not Path(xs).exists():
        return "UNAVAILABLE"
    h = hashlib.sha256(Path(xs).read_bytes()).hexdigest()
    return h[:16]


def build(model_name, config, seed, temperature, sab):
    if model_name == "unitcell":
        g, m, cells = geo.unit_cell(temperature)
        s = st.unit_cell_settings(config, geo.PITCH, geo.CELL_HALF_Z, seed=seed)
        return g, m, s, tal.unit_cell_tallies(cells), None

    if model_name == "core":
        g, m, cells, _ = geo.lattice_core(temperature)
    elif model_name == "core_homog":
        g, m, cells = geo.homogenized_core(temperature, sab=sab)
    else:
        raise ValueError(f"unknown model {model_name}")

    s = st.core_settings(
        config, geo.CORE_DIAMETER / 2.0, geo.CORE_HEIGHT, seed=seed
    )
    t, mesh = tal.core_tallies(
        cells["core"], geo.CORE_DIAMETER / 2.0, geo.CORE_HEIGHT
    )
    if "pin_fuel" in cells:
        t.append(tal.pin_power_tally(cells["pin_fuel"]))
    return g, m, s, t, mesh


def main():
    p = argparse.ArgumentParser()
    p.add_argument("model", choices=["unitcell", "core", "core_homog"])
    p.add_argument("config", choices=list(CONFIGS))
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--temperature", type=float, default=mat.REF_TEMPERATURE)
    p.add_argument("--threads", type=int, default=os.cpu_count())
    p.add_argument("--sab", choices=["zrh", "h2o", "none"], default="zrh",
                   help="homogenized-core hydrogen kernel (core_homog only)")
    args = p.parse_args()

    config = CONFIGS[args.config]
    tag = f"{args.model}_{args.config}_seed{args.seed}"
    if args.model == "core_homog":
        tag += f"_{args.sab}"
    rundir = ROOT / "run" / tag
    rundir.mkdir(parents=True, exist_ok=True)

    g, m, s, t, mesh = build(args.model, config, args.seed, args.temperature, args.sab)

    cwd = Path.cwd()
    os.chdir(rundir)
    try:
        m.export_to_xml()
        g.export_to_xml()
        s.export_to_xml()
        t.export_to_xml()

        os.environ["OMP_NUM_THREADS"] = str(args.threads)
        t0 = time.time()
        openmc.run()
        wall = time.time() - t0

        sp_path = Path(f"statepoint.{config['batches']}.h5")
        with openmc.StatePoint(sp_path) as sp:
            k = sp.keff
            k_val, k_std = float(k.nominal_value), float(k.std_dev)
            entropy = list(map(float, sp.entropy)) if sp.entropy is not None else []
    finally:
        os.chdir(cwd)

    label = "k_inf" if args.model == "unitcell" else "k_eff"
    record = {
        "model": args.model,
        "quantity": label,
        "value": f"{k_val:.6f}",
        "std_dev": f"{k_std:.6f}",
        "std_dev_pcm": f"{k_std * 1e5:.1f}",
        "config": args.config,
        "particles": config["particles"],
        "inactive_batches": config["inactive"],
        "active_batches": config["batches"] - config["inactive"],
        "total_batches": config["batches"],
        "histories": config["particles"] * config["batches"],
        "seed": args.seed,
        "sab": args.sab if args.model == "core_homog" else "per-material",
        "temperature_K": args.temperature,
        "threads": args.threads,
        "wall_clock_s": f"{wall:.1f}",
        "openmc_python": openmc.__version__,
        "nuclear_data": "ENDF/B-VIII.0",
        "xs_sha256_16": library_checksum(),
        "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    RESULTS.mkdir(exist_ok=True)
    csv_path = RESULTS / f"pcm_openmc_{args.model}.csv"
    write_header = not csv_path.exists()
    with open(csv_path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(record))
        if write_header:
            w.writeheader()
        w.writerow(record)

    if entropy:
        with open(RESULTS / f"entropy_{args.model}_{args.config}_seed{args.seed}.json", "w") as fh:
            json.dump({"shannon_entropy": entropy}, fh)

    print(f"\n{'=' * 52}")
    print(f"pcM {args.model} [{args.config}]")
    print(f"  {label} = {k_val:.6f} +/- {k_std:.6f}  ({k_std * 1e5:.1f} pcm)")
    print(f"  histories: {record['histories']:,}   wall: {wall:.1f} s")
    print(f"  -> {csv_path.relative_to(ROOT)}")
    print(f"{'=' * 52}")


if __name__ == "__main__":
    main()
