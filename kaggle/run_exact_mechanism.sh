#!/usr/bin/env bash
# E1/E2/E3a diagnostics only. No screen qualification, confirmation, or test access.
set -euo pipefail
: "${HIBERMEM_REF:?Set the full committed source revision}"
: "${HIBERMEM_CANDIDATE:?Choose qwen or phi}"
: "${HIBERMEM_EXPERIMENT:?Choose e1, e2, e3_core, or e3_presentation}"
[[ "${HIBERMEM_REF}" =~ ^[0-9a-f]{40}$ ]] || exit 2
[[ "${HIBERMEM_CANDIDATE}" == qwen || "${HIBERMEM_CANDIDATE}" == phi ]] || exit 2
case "${HIBERMEM_EXPERIMENT}" in
  e1|e2) ;;
  e3_core|e3_presentation)
    [[ "${HIBERMEM_CANDIDATE}" == qwen ]] || { echo "E3a freezes Qwen only" >&2; exit 2; } ;;
  *) exit 2 ;;
esac
[[ -d /kaggle/working ]] || { echo "Kaggle is required" >&2; exit 2; }
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
[[ "$(git rev-parse HEAD)" == "${HIBERMEM_REF}" ]] || { echo "Source commit mismatch" >&2; exit 2; }
[[ -z "$(git status --porcelain --untracked-files=all)" ]] || { echo "Commit source/config before running" >&2; exit 2; }

BASE_PYTHON="$(python -c 'import sys; print(sys.executable)')"
RUN_PARENT="results/exact_mechanism/${HIBERMEM_EXPERIMENT}-${HIBERMEM_CANDIDATE}"
RUN_DIR="${RUN_PARENT}/run"
CONFIG="configs/experiments/exact_mechanism_${HIBERMEM_EXPERIMENT}.json"
ARTIFACT="/kaggle/working/hibermem-exact-${HIBERMEM_EXPERIMENT}-${HIBERMEM_CANDIDATE}-${HIBERMEM_REF:0:12}-$(date -u +%Y%m%dT%H%M%SZ)-$$.tar.gz"
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
import json
import pathlib
import sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
    "stage": sys.argv[2], "raw_exit": int(sys.argv[3]), "exit": int(sys.argv[4]),
    "outcome": "validated_development_diagnostic" if sys.argv[4] == "0" else "infrastructure_error",
    "qualified": None, "scientific_gate_eligible": False,
    "confirmation_compatible": False, "selected_candidate": None,
}, indent=2))
PY
  local status_write="$?"
  [[ "${status_write}" == 0 ]] || status=2
  if ! tar -czf "${ARTIFACT}" "${RUN_PARENT}"; then
    echo "Archive failed; preserve ${RUN_PARENT} manually" >&2
    exit 2
  fi
  echo "Download: ${ARTIFACT}"
  echo "Exit ${status}: 0=validated completed diagnostic; 2=infrastructure/error. Neither means qualification."
  echo "Confirmation and test remain locked."
  exit "${status}"
}
trap 'finish "$?"' EXIT

BASE_TORCH="$("${BASE_PYTHON}" -c 'import torch; print(torch.__version__)')"
ENV_DIR="/kaggle/working/hibermem-exact-env-nopip"
ENV_PYTHON="${ENV_DIR}/bin/python"
if [[ ! -e "${ENV_DIR}" ]]; then
  "${BASE_PYTHON}" -m venv --without-pip --system-site-packages "${ENV_DIR}" \
    2>&1 | tee "${RUN_PARENT}/bootstrap.log"
fi
[[ -x "${ENV_PYTHON}" && -f "${ENV_DIR}/pyvenv.cfg" ]] || { echo "Incomplete environment; preserve it and use a fresh notebook" >&2; exit 2; }
"${ENV_PYTHON}" -c 'import pathlib, sys; assert pathlib.Path(sys.prefix) == pathlib.Path(sys.argv[1])' "${ENV_DIR}"
export HF_HOME="/kaggle/working/hf-cache-hibermem-v2-${HIBERMEM_CANDIDATE}"
export HIBERMEM_MIN_FREE_STORAGE_GIB="${HIBERMEM_MIN_FREE_STORAGE_GIB:-15}"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
STAGE="dependency_install"
"${BASE_PYTHON}" -m pip --python "${ENV_PYTHON}" install \
  -r configs/requirements/kaggle-phase2r-v2.txt -e '.[dev,reference]' \
  2>&1 | tee "${RUN_PARENT}/install.log"
STAGE="environment_check"
[[ "$("${ENV_PYTHON}" -c 'import torch; print(torch.__version__)')" == "${BASE_TORCH}" ]] || { echo "PyTorch changed unexpectedly" >&2; exit 2; }
"${BASE_PYTHON}" -m pip --python "${ENV_PYTHON}" freeze > "${RUN_PARENT}/packages.txt"
"${ENV_PYTHON}" scripts/verify_kaggle_environment.py --output "${RUN_PARENT}/environment.json"
STAGE="tests"
"${ENV_PYTHON}" scripts/run_tests.py -q --junitxml "${RUN_PARENT}/tests.xml" \
  2>&1 | tee "${RUN_PARENT}/tests.log"
STAGE="controls"
"${ENV_PYTHON}" scripts/run_exact_mechanism.py --config "${CONFIG}" --controls-only \
  2>&1 | tee "${RUN_PARENT}/controls.log"
STAGE="diagnostic"
"${ENV_PYTHON}" -u scripts/run_exact_mechanism.py --config "${CONFIG}" \
  --candidate "${HIBERMEM_CANDIDATE}" --run-dir "${RUN_DIR}" \
  2>&1 | tee "${RUN_PARENT}/run.log"
STAGE="artifact_validation"
"${ENV_PYTHON}" scripts/validate_exact_mechanism.py --report "${RUN_DIR}/report.json"
VALIDATED=1
STAGE="complete"
