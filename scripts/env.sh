#!/usr/bin/env bash
# pcM environment. Source this before any run:  source scripts/env.sh
#
# Absolute paths are used deliberately: `conda activate` is unreliable in
# non-interactive shells on this machine, and pinning paths makes runs
# reproducible.

export CARDINAL_DIR="/Users/kavyawadhwa/MOOSE/cardinal"
export CONDA_ROOT="/Users/kavyawadhwa/Anaconda/anaconda3"

# Cardinal's own OpenMC build (0.15.4-dev190, commit 66359e5dd) is the solver.
# The other openmc binaries on this machine are broken (dyld symbol errors).
export PATH="${CARDINAL_DIR}/install/bin:${PATH}"
export DYLD_LIBRARY_PATH="${CARDINAL_DIR}/install/lib:${DYLD_LIBRARY_PATH:-}"

# OpenMC Python API (0.15.1.dev0) - input generation only
export PCM_PYTHON="${CONDA_ROOT}/envs/openmc/bin/python"

export OPENMC_CROSS_SECTIONS="/Users/kavyawadhwa/Documents/Digital Twin/nuclear_data/endfb-viii.0-hdf5/cross_sections.xml"

# 8 physical cores on the Apple M2 (spec/hardware.md)
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"

export PCM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
