#!/usr/bin/env bash
# pcM standalone NekRS run.
#
#   ./scripts/run_nekrs.sh [ranks]
#
# Defaults to all physical cores. NEVER run this on a single rank: Nek5000
# allocates statically with lelt = elements-per-rank, so one rank puts the
# whole mesh into one translation unit and the JIT Fortran compile can exhaust
# RAM (this killed an 8 GiB machine at 2880 elements / 4.25 GB). See
# docs/PORTING.md for the arithmetic.
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

RANKS="${1:-${PCM_CORES}}"
CASE="${PCM_NEK_CASE:-fluid}"
# CARDINAL on the Binder image was built against the system MPICH.  A Conda
# MPI launcher can start several singleton processes instead of one MPI job.
# Allow an override for other machines, but prefer the matching launcher here.
MPIEXEC="${PCM_MPIEXEC:-/usr/bin/mpirun}"
# CARDINAL was linked with the system MPICH.  notebook's Conda environment
# also ships MPI libraries; if it appears first in LD_LIBRARY_PATH, MPICH's
# launcher creates isolated singleton processes. Keep the linked MPICH first.
SYSTEM_MPICH_LIB="/usr/lib/x86_64-linux-gnu/mpich/lib"
cd "${PCM_ROOT}/cardinal/nekrs"

if [ "${RANKS}" -lt 1 ]; then
  echo "ERROR: rank count must be positive." >&2
  exit 1
fi

if [ "${RANKS}" -eq 1 ] && [ "${PCM_ALLOW_SERIAL_NEKRS:-no}" != "yes" ]; then
  echo "ERROR: refusing a single-rank NekRS run by default." >&2
  echo "       It sets lelt = total elements and can exhaust memory during JIT." >&2
  echo "       On a verified high-memory machine, set PCM_ALLOW_SERIAL_NEKRS=yes" >&2
  echo "       to make an intentional serial fallback run." >&2
  exit 1
fi

if [ ! -f "${CASE}.re2" ]; then
  echo "ERROR: ${CASE}.re2 missing. Regenerate it with:" >&2
  echo "       cardinal-opt -i fluid.i --mesh-only" >&2
  echo "       cardinal-opt -i convert.i --mesh-only && mv convert_in.e convert.exo" >&2
  echo "       printf '1\\nconvert\\n0\\n0\\n${CASE}\\n' | exo2nek" >&2
  exit 1
fi

if [ ! -x "${MPIEXEC}" ]; then
  echo "ERROR: MPI launcher not executable: ${MPIEXEC}" >&2
  echo "       Set PCM_MPIEXEC to the mpirun matching your CARDINAL build." >&2
  exit 1
fi

echo "case=${CASE} ranks=${RANKS} backend=${PCM_NEKRS_BACKEND} mem=${PCM_MEM_GB}GiB"

if [ -d "${SYSTEM_MPICH_LIB}" ]; then
  export LD_LIBRARY_PATH="${SYSTEM_MPICH_LIB}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
fi

# Keep separately reusable caches for each backend and rank count. Set
# PCM_NEKRS_CLEAN_CACHE=yes only when changing mesh/order or recovering from a
# failed JIT compilation; normal reruns should reuse the expensive GPU kernels.
CACHE_BACKEND="$(printf '%s' "${PCM_NEKRS_BACKEND}" | tr '[:upper:]' '[:lower:]')"
CACHE_TAG="${CACHE_BACKEND}-np${RANKS}"
export NEKRS_CACHE_DIR="${PCM_NEKRS_CACHE_DIR:-${PCM_ROOT}/cardinal/nekrs/.cache/${CACHE_TAG}}"
export OCCA_CACHE_DIR="${PCM_OCCA_CACHE_DIR:-${HOME}/.cache/occa/${CACHE_TAG}}"

if [ "${PCM_NEKRS_CLEAN_CACHE:-no}" = "yes" ]; then
  rm -rf -- "${NEKRS_CACHE_DIR}" "${OCCA_CACHE_DIR}"
fi
mkdir -p "${NEKRS_CACHE_DIR}" "${OCCA_CACHE_DIR}"
echo "nekrs cache=${NEKRS_CACHE_DIR}"
echo "occa cache=${OCCA_CACHE_DIR}"

if [ "${RANKS}" -eq 1 ]; then
  echo "WARNING: intentional serial fallback; no MPI acceleration is available."
  exec "${NEKRS_HOME}/bin/nekrs" \
    --setup "${CASE}.par" --backend "${PCM_NEKRS_BACKEND}"
fi

echo "mpi launcher=${MPIEXEC}"
exec "${MPIEXEC}" -np "${RANKS}" "${NEKRS_HOME}/bin/nekrs" \
  --setup "${CASE}.par" --backend "${PCM_NEKRS_BACKEND}"
