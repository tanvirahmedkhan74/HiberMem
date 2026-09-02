#!/usr/bin/env bash
# E4 design-cohort development run only. Historical P2 confirmation/test are inaccessible.
set -euo pipefail
: "${HIBERMEM_REF:?Set the full committed source revision}"
: "${HIBERMEM_E4_CONFIG:?Set the committed frozen E4 config path}"
[[ "${HIBERMEM_REF}" =~ ^[0-9a-f]{40}$ ]] || exit 2
[[ -d /kaggle/working ]] || { echo "Kaggle is required" >&2; exit 2; }
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
[[ "$(git rev-parse HEAD)" == "${HIBERMEM_REF}" ]] || { echo "Source commit mismatch" >&2; exit 2; }
[[ -z "$(git status --porcelain --untracked-files=all)" ]] || { echo "Commit source/frozen config before running" >&2; exit 2; }
[[ -f "${HIBERMEM_E4_CONFIG}" ]] || { echo "Frozen config not found" >&2; exit 2; }

BASE_PYTHON="$(python -c 'import sys; print(sys.executable)')"
RUN_PARENT="results/e4_prospective/qwen-design"
RUN_DIR="${RUN_PARENT}/run"
ARTIFACT="/kaggle/working/hibermem-e4-qwen-${HIBERMEM_REF:0:12}-$(date -u +%Y%m%dT%H%M%SZ)-$$.tar.gz"
STAGE="environment_setup"
VALIDATED=0
mkdir -p "${RUN_PARENT}"
finish() {
  local raw_status="$1"
  trap - EXIT
  set +e
  local status=2
  [[ "${raw_status}" == 0 && "${VALIDATED}" == 1 && "${STAGE}" == complete ]] && status=0
  "${BASE_PYTHON}" - "${RUN_PARENT}/launcher-status.json" "${STAGE}" "${raw_status}" "${status}" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
    "stage": sys.argv[2], "raw_exit": int(sys.argv[3]), "exit": int(sys.argv[4]),
    "outcome": "validated_prospective_development" if sys.argv[4] == "0" else "infrastructure_error",
    "qualified": None, "scientific_gate_eligible": False,
    "confirmation_compatible": False, "test_access": False,
}, indent=2))
PY
  [[ "$?" == 0 ]] || status=2
  tar -czf "${ARTIFACT}" "${RUN_PARENT}" || { echo "Archive failed; preserve ${RUN_PARENT}" >&2; exit 2; }
  echo "Download: ${ARTIFACT}"
  echo "Exit ${status}: 0=validated E4 development run; 2=setup/test/runtime error."
  echo "No P2/P3 decision. Historical confirmation and test remain locked."
  exit "${status}"
}
trap 'finish "$?"' EXIT

BASE_TORCH="$("${BASE_PYTHON}" -c 'import torch; print(torch.__version__)')"
ENV_DIR="/kaggle/working/hibermem-e4-env-nopip"
ENV_PYTHON="${ENV_DIR}/bin/python"
if [[ ! -e "${ENV_DIR}" ]]; then
  "${BASE_PYTHON}" -m venv --without-pip --system-site-packages "${ENV_DIR}" \
    2>&1 | tee "${RUN_PARENT}/bootstrap.log"
fi
[[ -x "${ENV_PYTHON}" && -f "${ENV_DIR}/pyvenv.cfg" ]] || exit 2
export HF_HOME="/kaggle/working/hf-cache-hibermem-qwen"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
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
"${ENV_PYTHON}" scripts/run_e4_prospective.py --config "${HIBERMEM_E4_CONFIG}" \
  --candidate qwen --controls-only 2>&1 | tee "${RUN_PARENT}/controls.log"
STAGE="past"
"${ENV_PYTHON}" -u scripts/run_e4_prospective.py --config "${HIBERMEM_E4_CONFIG}" \
  --candidate qwen --stage past --run-dir "${RUN_DIR}" 2>&1 | tee "${RUN_PARENT}/past.log"
STAGE="past_validation"
"${ENV_PYTHON}" scripts/validate_e4_report.py --run-dir "${RUN_DIR}" --stage past
STAGE="freeze"
"${ENV_PYTHON}" scripts/run_e4_prospective.py --config "${HIBERMEM_E4_CONFIG}" \
  --candidate qwen --stage freeze --run-dir "${RUN_DIR}" 2>&1 | tee "${RUN_PARENT}/freeze.log"
STAGE="future"
"${ENV_PYTHON}" -u scripts/run_e4_prospective.py --config "${HIBERMEM_E4_CONFIG}" \
  --candidate qwen --stage future --run-dir "${RUN_DIR}" 2>&1 | tee "${RUN_PARENT}/future.log"
STAGE="artifact_validation"
"${ENV_PYTHON}" scripts/validate_e4_report.py --run-dir "${RUN_DIR}" --stage complete
VALIDATED=1
STAGE="complete"
