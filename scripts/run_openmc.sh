#!/usr/bin/env bash
# Standalone OpenMC runs.
#   ./scripts/run_openmc.sh unitcell baseline [--seed 1]
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

cd "${TRIGA_ROOT}/cardinal/openmc"
exec "${TRIGA_PYTHON}" run.py "$@"
