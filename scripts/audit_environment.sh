#!/usr/bin/env bash
# pcM Phase 0 environment audit. Run this FIRST on any new machine:
#
#   ./scripts/audit_environment.sh
#
# Reports what was found and what is missing. Anything marked MISSING must be
# resolved before that part of the workflow can run. Record the output in
# spec/hardware.md for the new machine.

source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

ok()   { printf '  \033[32mOK\033[0m      %s\n' "$1"; }
miss() { printf '  \033[31mMISSING\033[0m %s\n' "$1"; FAILED=$((FAILED+1)); }
warn() { printf '  \033[33mWARN\033[0m    %s\n' "$1"; }
FAILED=0

echo "=============================================="
echo " pcM environment audit"
echo "=============================================="

echo
echo "--- Hardware / OS ---"
if [ "${PCM_OS}" = linux ]; then
  echo "  distro:  $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME")"
  echo "  kernel:  $(uname -r)"
  echo "  cpu:     $(awk -F: '/model name/{print $2; exit}' /proc/cpuinfo | sed 's/^ *//')"
else
  echo "  macOS:   $(sw_vers -productVersion 2>/dev/null)"
  echo "  cpu:     $(sysctl -n machdep.cpu.brand_string 2>/dev/null)"
fi
echo "  cores:   ${PCM_CORES} physical"
echo "  memory:  ${PCM_MEM_GB} GiB"

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null \
    | while read -r g; do ok "GPU: $g"; done
else
  echo "  gpu:     no nvidia-smi (NekRS stays CPU-only)"
fi
echo "  NekRS backend selected: ${PCM_NEKRS_BACKEND}"

echo
echo "--- Cardinal ---"
if [ -n "${CARDINAL_DIR}" ] && [ -d "${CARDINAL_DIR}" ]; then
  ok "CARDINAL_DIR = ${CARDINAL_DIR}"
  if command -v cardinal-opt >/dev/null 2>&1; then
    ok "cardinal-opt = $(command -v cardinal-opt)"
  else
    miss "cardinal-opt not on PATH (expected ${CARDINAL_DIR}/cardinal-opt)"
  fi
else
  miss "Cardinal not found. Set PCM_CARDINAL_DIR=/path/to/cardinal"
fi

echo
echo "--- OpenMC ---"
if command -v openmc >/dev/null 2>&1; then
  ok "openmc solver = $(command -v openmc) ($(openmc --version 2>&1 | head -1))"
else
  warn "openmc binary not on PATH (Cardinal runs OpenMC internally, so this is optional)"
fi
if "${PCM_PYTHON}" -c 'import openmc' >/dev/null 2>&1; then
  ok "openmc python = ${PCM_PYTHON} ($("${PCM_PYTHON}" -c 'import openmc;print(openmc.__version__)'))"
else
  miss "openmc Python API not importable by ${PCM_PYTHON} (needed to build inputs)"
fi

echo
echo "--- Nuclear data ---"
if [ -n "${OPENMC_CROSS_SECTIONS:-}" ] && [ -f "${OPENMC_CROSS_SECTIONS}" ]; then
  ok "cross_sections.xml = ${OPENMC_CROSS_SECTIONS}"
  for t in c_H_in_ZrH c_Zr_in_ZrH; do
    d="$(dirname "${OPENMC_CROSS_SECTIONS}")/thermal/${t}.h5"
    [ -f "$d" ] && ok "S(a,b) ${t}" || miss "S(a,b) ${t} - required for TRIGA ZrH feedback"
  done
else
  miss "ENDF/B-VIII.0 not found. Set PCM_CROSS_SECTIONS=/path/to/cross_sections.xml"
fi

echo
echo "--- NekRS ---"
if [ -n "${NEKRS_HOME:-}" ] && [ -x "${NEKRS_HOME}/bin/nekrs" ]; then
  ok "nekrs = ${NEKRS_HOME}/bin/nekrs"
else
  miss "nekrs binary not found under NEKRS_HOME=${NEKRS_HOME:-unset}"
fi
# NekRS JIT-builds a Fortran interface; without this the build dies midway.
if command -v mpifort >/dev/null 2>&1; then
  if mpifort -show >/dev/null 2>&1; then
    ok "mpifort works ($(mpifort -show 2>/dev/null | awk '{print $1}'))"
  else
    miss "mpifort present but its backend compiler is missing - NekRS JIT build WILL fail"
  fi
else
  miss "mpifort not found - NekRS cannot JIT-build its Nek5000 interface"
fi
if command -v exo2nek >/dev/null 2>&1 || [ -x "$HOME/Nek5000/bin/exo2nek" ]; then
  ok "exo2nek available"
else
  warn "exo2nek not found - only needed to regenerate cardinal/nekrs/fluid.re2"
  echo "          build: git clone https://github.com/Nek5000/Nek5000.git && cd Nek5000/tools && ./maketools exo2nek"
fi

echo
echo "--- NekRS sizing guidance (memory) ---"
# Nek5000 allocates statically: ~854 arrays of (lx1^3 * lelt) doubles, where
# lelt = elements per RANK. Running on 1 rank puts the whole mesh in one
# translation unit and the JIT compile can exhaust RAM. See docs/PORTING.md.
ELEMS="${PCM_NEK_ELEMENTS:-2880}"
POLY="${PCM_NEK_POLY:-5}"
"${PCM_PYTHON}" - "$ELEMS" "$POLY" "$PCM_CORES" "$PCM_MEM_GB" <<'PY'
import sys
elems, poly, cores, mem = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
lx1 = poly + 1; arrays = 854
print(f"  mesh {elems} elems, polynomialOrder {poly} (lx1={lx1}), {cores} cores, {mem} GiB")
for r in sorted({1, 2, 4, cores}):
    if r < 1: continue
    lelt = -(-elems // r)
    per = arrays * lx1**3 * lelt * 8 / 1e9
    flag = "  <-- single rank: avoid" if r == 1 else ""
    print(f"    {r:2d} rank(s): lelt={lelt:5d}  {per:6.2f} GB/rank  {per*r:6.2f} GB total{flag}")
print(f"  Recommend: mpirun -np {max(2, cores)} (keeps lelt small enough to compile)")
PY

echo
echo "=============================================="
if [ "$FAILED" -eq 0 ]; then
  echo " All required components found."
else
  echo " ${FAILED} required component(s) MISSING - see above."
fi
echo "=============================================="
exit 0
