#!/usr/bin/env bash
# pcM standalone OpenMC runs.
#   ./scripts/run_openmc.sh unitcell baseline [--seed 1]
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

cd "${PCM_ROOT}/cardinal/openmc"
exec "${PCM_PYTHON}" run.py "$@"
