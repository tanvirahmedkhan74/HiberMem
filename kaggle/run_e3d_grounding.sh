#!/usr/bin/env bash
# E3d measurement-instrument qualification. Never runs E4 or historical test data.
set -euo pipefail
: "${HIBERMEM_REF:?Set the full committed source revision}"
[[ "${HIBERMEM_REF}" =~ ^[0-9a-f]{40}$ ]] || exit 2
[[ -d /kaggle/working ]] || { echo "Kaggle is required" >&2; exit 2; }
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
[[ "$(git rev-parse HEAD)" == "${HIBERMEM_REF}" ]] || { echo "Source commit mismatch" >&2; exit 2; }
[[ -z "$(git status --porcelain --untracked-files=all)" ]] || { echo "Commit source/config before running" >&2; exit 2; }

BASE_PYTHON="$(python -c 'import sys; print(sys.executable)')"
CONFIG="${HIBERMEM_E3D_CONFIG:-configs/experiments/e3d_grounding_development.json}"
STAGE_NAME="$("${BASE_PYTHON}" -c 'import json,sys; print(json.load(open(sys.argv[1]))["stage"])' "${CONFIG}")"
[[ "${STAGE_NAME}" == development || "${STAGE_NAME}" == verification ]] || exit 2
RUN_PARENT="results/e3d_grounding/${STAGE_NAME}/qwen"
RUN_DIR="${RUN_PARENT}/run"
DEVELOPMENT_REPORT="${HIBERMEM_E3D_DEVELOPMENT_REPORT:-results/e3d_grounding/development/qwen/run/report.json}"
ARTIFACT="/kaggle/working/hibermem-e3d-${STAGE_NAME}-qwen-${HIBERMEM_REF:0:12}-$(date -u +%Y%m%dT%H%M%SZ)-$$.tar.gz"
STAGE="environment_setup"
VALIDATED=0
mkdir -p "${RUN_PARENT}"

finish() {
  local raw_status="$1"
  trap - EXIT
  set +e
  local status=2
  [[ "${raw_status}" == 0 && "${VALIDATED}" == 1 && "${STAGE}" == complete ]] && status=0
  "${BASE_PYTHON}" - "${RUN_PARENT}/launcher-status.json" "${STAGE}" "${raw_status}" "${status}" "${STAGE_NAME}" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
    "stage": sys.argv[2], "raw_exit": int(sys.argv[3]), "exit": int(sys.argv[4]),
    "e3d_stage": sys.argv[5],
    "outcome": "validated_measurement_diagnostic" if sys.argv[4] == "0" else "infrastructure_error",
    "scientific_gate_eligible": False, "retention_result": False,
    "confirmation_compatible": False, "historical_test_access": False,
}, indent=2))
PY
  [[ "$?" == 0 ]] || status=2
  tar -czf "${ARTIFACT}" results/e3d_grounding || {
    echo "Archive failed; preserve results/e3d_grounding" >&2
    exit 2
  }
  echo "Download: ${ARTIFACT}"
  echo "Exit ${status}: 0=validated E3d artifact; 2=setup/test/runtime error."
  echo "No automatic selection, E4 execution, confirmation, or historical-test access."
  exit "${status}"
}
trap 'finish "$?"' EXIT

BASE_TORCH="$("${BASE_PYTHON}" -c 'import torch; print(torch.__version__)')"
ENV_DIR="/kaggle/working/hibermem-e3d-env-nopip"
ENV_PYTHON="${ENV_DIR}/bin/python"
if [[ ! -e "${ENV_DIR}" ]]; then
  "${BASE_PYTHON}" -m venv --without-pip --system-site-packages "${ENV_DIR}" \
    2>&1 | tee "${RUN_PARENT}/bootstrap.log"
fi
[[ -x "${ENV_PYTHON}" && -f "${ENV_DIR}/pyvenv.cfg" ]] || exit 2
export HF_HOME="/kaggle/working/hf-cache-hibermem-qwen"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
export HIBERMEM_MIN_FREE_STORAGE_GIB="${HIBERMEM_MIN_FREE_STORAGE_GIB:-15}"

STAGE="dependency_install"
"${BASE_PYTHON}" -m pip --python "${ENV_PYTHON}" install \
  -r configs/requirements/kaggle-phase2r-v2.txt -e '.[dev,reference]' \
  2>&1 | tee "${RUN_PARENT}/install.log"
STAGE="environment_check"
[[ "$("${ENV_PYTHON}" -c 'import torch; print(torch.__version__)')" == "${BASE_TORCH}" ]] || exit 2
"${BASE_PYTHON}" -m pip --python "${ENV_PYTHON}" freeze > "${RUN_PARENT}/packages.txt"
"${ENV_PYTHON}" scripts/verify_kaggle_environment.py --output "${RUN_PARENT}/environment.json"
STAGE="tests"
"${ENV_PYTHON}" scripts/run_tests.py -q --junitxml "${RUN_PARENT}/tests.xml" \
  2>&1 | tee "${RUN_PARENT}/tests.log"
STAGE="controls"
"${ENV_PYTHON}" scripts/run_e3d_grounding.py --config "${CONFIG}" --controls-only \
  2>&1 | tee "${RUN_PARENT}/controls.log"

RUN_ARGS=(--config "${CONFIG}" --candidate qwen --run-dir "${RUN_DIR}")
VALIDATE_ARGS=(--report "${RUN_DIR}/report.json")
if [[ "${STAGE_NAME}" == verification ]]; then
  [[ -f "${DEVELOPMENT_REPORT}" ]] || {
    echo "Verification requires the bound development artifact" >&2
    exit 2
  }
  RUN_ARGS+=(--development-report "${DEVELOPMENT_REPORT}")
  VALIDATE_ARGS+=(--development-report "${DEVELOPMENT_REPORT}")
fi
STAGE="diagnostic"
"${ENV_PYTHON}" -u scripts/run_e3d_grounding.py "${RUN_ARGS[@]}" \
  2>&1 | tee "${RUN_PARENT}/run.log"
STAGE="artifact_validation"
"${ENV_PYTHON}" scripts/validate_e3d_report.py "${VALIDATE_ARGS[@]}"
VALIDATED=1
STAGE="complete"
