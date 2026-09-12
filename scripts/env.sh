#!/usr/bin/env bash
# pcM environment. Source before any run:  source scripts/env.sh
#
# Portable across macOS and Linux. Everything is auto-detected, and every
# value can be overridden by exporting it before sourcing, e.g.
#
#   export PCM_CARDINAL_DIR=$HOME/cardinal
#   export PCM_CROSS_SECTIONS=$HOME/data/endfb-viii.0-hdf5/cross_sections.xml
#   source scripts/env.sh
#
# Run scripts/audit_environment.sh to check what was found.

export PCM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

case "$(uname -s)" in
  Darwin) PCM_OS=macos ;;
  Linux)  PCM_OS=linux ;;
  *)      PCM_OS=unknown ;;
esac
export PCM_OS

_pcm_first_dir() { for d in "$@"; do [ -d "$d" ] && { echo "$d"; return; }; done; }
_pcm_first_file() { for f in "$@"; do [ -f "$f" ] && { echo "$f"; return; }; done; }

# ---------------------------------------------------------------- Cardinal
# Located by (1) PCM_CARDINAL_DIR, (2) CARDINAL_DIR, (3) cardinal-opt on PATH,
# (4) common install locations.
if [ -n "${PCM_CARDINAL_DIR:-}" ]; then
  CARDINAL_DIR="${PCM_CARDINAL_DIR}"
elif [ -n "${CARDINAL_DIR:-}" ]; then
  :
elif command -v cardinal-opt >/dev/null 2>&1; then
  CARDINAL_DIR="$(cd "$(dirname "$(command -v cardinal-opt)")" && pwd)"
else
  CARDINAL_DIR="$(_pcm_first_dir \
    "$HOME/cardinal" "$HOME/projects/cardinal" "$HOME/MOOSE/cardinal" \
    "$HOME/moose/cardinal" "/opt/cardinal" "/usr/local/cardinal")"
fi
export CARDINAL_DIR

if [ -n "${CARDINAL_DIR}" ] && [ -d "${CARDINAL_DIR}" ]; then
  export PATH="${CARDINAL_DIR}:${CARDINAL_DIR}/install/bin:${PATH}"
  export NEKRS_HOME="${NEKRS_HOME:-${CARDINAL_DIR}/install}"
  if [ "${PCM_OS}" = macos ]; then
    export DYLD_LIBRARY_PATH="${CARDINAL_DIR}/install/lib:${DYLD_LIBRARY_PATH:-}"
  else
    export LD_LIBRARY_PATH="${CARDINAL_DIR}/install/lib:${LD_LIBRARY_PATH:-}"
  fi
fi

# ------------------------------------------------------------------- conda
# NekRS JIT-compiles a Nek5000 interface at run time and needs a Fortran
# compiler. On a conda-based MOOSE install the toolchain lives in the env's
# bin (macOS: arm64-apple-darwin*-gfortran, Linux: x86_64-conda-linux-gnu-*),
# so that directory must be on PATH or the NekRS build fails with
# "command not found" partway through.
if [ -z "${CONDA_ROOT:-}" ]; then
  if [ -n "${CONDA_EXE:-}" ]; then
    CONDA_ROOT="$(cd "$(dirname "$(dirname "${CONDA_EXE}")")" && pwd)"
  elif command -v conda >/dev/null 2>&1; then
    CONDA_ROOT="$(conda info --base 2>/dev/null)"
  else
    CONDA_ROOT="$(_pcm_first_dir \
      "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3" \
      "$HOME/mambaforge" "$HOME/Anaconda/anaconda3" "/opt/conda")"
  fi
fi
export CONDA_ROOT

PCM_MOOSE_ENV="${PCM_MOOSE_ENV:-moose}"
if [ -n "${CONDA_ROOT}" ] && [ -d "${CONDA_ROOT}/envs/${PCM_MOOSE_ENV}/bin" ]; then
  export PATH="${PATH}:${CONDA_ROOT}/envs/${PCM_MOOSE_ENV}/bin"
fi

# ------------------------------------------------------- Python for OpenMC
# Only used to generate inputs and post-process; the solver is Cardinal's.
if [ -z "${PCM_PYTHON:-}" ]; then
  for _cand in \
      "${CONDA_ROOT}/envs/openmc/bin/python" \
      "${CONDA_ROOT}/envs/${PCM_MOOSE_ENV}/bin/python" \
      "${CONDA_ROOT}/envs/cardinal/bin/python" \
      "$(command -v python3 2>/dev/null)"; do
    [ -x "${_cand}" ] || continue
    if "${_cand}" -c 'import openmc' >/dev/null 2>&1; then PCM_PYTHON="${_cand}"; break; fi
    [ -z "${_pcm_py_fallback:-}" ] && _pcm_py_fallback="${_cand}"
  done
  PCM_PYTHON="${PCM_PYTHON:-${_pcm_py_fallback:-python3}}"
fi
export PCM_PYTHON

# ----------------------------------------------------------- nuclear data
# ENDF/B-VIII.0 HDF5. Must be the official release (see spec/materials.md).
if [ -n "${PCM_CROSS_SECTIONS:-}" ]; then
  export OPENMC_CROSS_SECTIONS="${PCM_CROSS_SECTIONS}"
elif [ -z "${OPENMC_CROSS_SECTIONS:-}" ]; then
  # VIII.0 is the spec library and is searched first. VII.1 is what the
  # Binder/Cardinal image carries; it is found as a fallback, but see the
  # warning printed below - results from the two are NOT interchangeable.
  _xs="$(_pcm_first_file \
    "$HOME/cross_sections/endfb-viii.0-hdf5/cross_sections.xml" \
    "$HOME/nuclear_data/endfb-viii.0-hdf5/cross_sections.xml" \
    "$HOME/data/endfb-viii.0-hdf5/cross_sections.xml" \
    "$HOME/openmc_data/endfb-viii.0-hdf5/cross_sections.xml" \
    "$HOME/Documents/Digital Twin/nuclear_data/endfb-viii.0-hdf5/cross_sections.xml" \
    "/opt/nuclear_data/endfb-viii.0-hdf5/cross_sections.xml" \
    "/usr/share/openmc/endfb-viii.0-hdf5/cross_sections.xml" \
    "$HOME/cross_sections/endfb-vii.1-hdf5/cross_sections.xml" \
    "$HOME/nuclear_data/endfb-vii.1-hdf5/cross_sections.xml" \
    "/opt/nuclear_data/endfb-vii.1-hdf5/cross_sections.xml")"
  [ -n "${_xs}" ] && export OPENMC_CROSS_SECTIONS="${_xs}"
fi

# Record which library is actually in use. Every result must be labelled with
# it: the committed baselines were produced with VIII.0, and pcL used VIII.0.
case "${OPENMC_CROSS_SECTIONS:-}" in
  *viii.0*|*viii-0*|*b8*|*VIII.0*) export PCM_XS_LIBRARY="ENDF/B-VIII.0" ;;
  *vii.1*|*vii-1*|*b7*|*VII.1*)    export PCM_XS_LIBRARY="ENDF/B-VII.1" ;;
  "")                              export PCM_XS_LIBRARY="none-found" ;;
  *)                               export PCM_XS_LIBRARY="unidentified" ;;
esac

# --------------------------------------------------------------- hardware
if [ -z "${PCM_CORES:-}" ]; then
  if [ "${PCM_OS}" = macos ]; then
    PCM_CORES="$(sysctl -n hw.physicalcpu 2>/dev/null || echo 4)"
  else
    PCM_CORES="$(nproc 2>/dev/null || echo 4)"
  fi
fi
export PCM_CORES
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-${PCM_CORES}}"

if [ -z "${PCM_MEM_GB:-}" ]; then
  if [ "${PCM_OS}" = macos ]; then
    PCM_MEM_GB="$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))"
  else
    PCM_MEM_GB="$(awk '/MemTotal/{printf "%d", $2/1048576}' /proc/meminfo 2>/dev/null || echo 0)"
  fi
fi
export PCM_MEM_GB

# NekRS backend: CPU unless a supported GPU is demonstrated. Override with
# PCM_NEKRS_BACKEND=CUDA once nvidia-smi confirms a usable device.
if [ -z "${PCM_NEKRS_BACKEND:-}" ]; then
  if [ "${PCM_OS}" = linux ] && command -v nvidia-smi >/dev/null 2>&1 \
     && nvidia-smi -L 2>/dev/null | grep -q GPU; then
    PCM_NEKRS_BACKEND=CUDA
  else
    PCM_NEKRS_BACKEND=CPU
  fi
fi
export PCM_NEKRS_BACKEND

# Binder installs the CUDA runtime and math libraries in the MOOSE Conda
# environment rather than a system CUDA prefix. Make them visible to NekRS in
# fresh terminals. run_nekrs.sh still prepends the system MPICH directory, so
# this must not reintroduce Conda's singleton-MPI launcher/library mismatch.
if [ "${PCM_OS}" = linux ] && [ "${PCM_NEKRS_BACKEND}" = CUDA ] \
   && [ -d "${CONDA_ROOT}/envs/${PCM_MOOSE_ENV}/lib" ]; then
  export LD_LIBRARY_PATH="${CONDA_ROOT}/envs/${PCM_MOOSE_ENV}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
fi

unset _pcm_py_fallback _cand _xs
