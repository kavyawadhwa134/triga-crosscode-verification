#!/usr/bin/env bash
# pcM coupled Cardinal run (OpenMC <-> MOOSE heat conduction).
#
#   ./scripts/run_coupled.sh smoke           # 5 Picard steps, 5k particles
#   ./scripts/run_coupled.sh production      # 10 Picard steps, 20k particles
#   ./scripts/run_coupled.sh production 8    # ...on 8 MPI ranks
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

MODE="${1:-smoke}"
RANKS="${2:-1}"

case "${MODE}" in
  smoke)      PARTICLES=5000;  BATCHES=100; INACTIVE=25; STEPS=5  ;;
  production) PARTICLES=20000; BATCHES=150; INACTIVE=30; STEPS=10 ;;
  *) echo "usage: $0 [smoke|production] [ranks]" >&2; exit 1 ;;
esac

OUT="${PCM_ROOT}/run/coupled_${MODE}"
mkdir -p "${OUT}"

cd "${PCM_ROOT}/cardinal/coupling"

# The solid mesh must exist before either app can read it.
if [ ! -f "${PCM_ROOT}/cardinal/moose/pcm_solid_in.e" ]; then
  echo "building solid mesh..."
  (cd "${PCM_ROOT}/cardinal/moose" && cardinal-opt -i mesh.i --mesh-only pcm_solid_in.e)
fi

echo "generating 3-D OpenMC model (${PARTICLES} particles, ${BATCHES} batches)..."
"${PCM_PYTHON}" make_coupled_model.py -n 20 \
  --particles "${PARTICLES}" --batches "${BATCHES}" --inactive "${INACTIVE}"

echo "running coupled ${MODE}: ${STEPS} Picard steps, ${RANKS} rank(s)"
LAUNCH=(cardinal-opt)
[ "${RANKS}" -gt 1 ] && LAUNCH=(mpirun -np "${RANKS}" cardinal-opt)

"${LAUNCH[@]}" -i solid.i \
  Executioner/num_steps="${STEPS}" \
  Outputs/file_base="${OUT}/solid" \
  2>&1 | tee "${OUT}/run.log"

echo
echo "results in ${OUT}"
grep -A20 'Postprocessor Values' "${OUT}/run.log" | tail -15 || true
