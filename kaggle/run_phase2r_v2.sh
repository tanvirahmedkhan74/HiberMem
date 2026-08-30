#!/usr/bin/env bash
# Run from an already checked-out exact HiberMem commit. No git pull, resets,
# model-cache deletion, confirmation, or test-unlock operations are performed.
set -euo pipefail

: "${HIBERMEM_REF:?Set HIBERMEM_REF to the exact 40-character source commit}"
: "${HIBERMEM_CANDIDATE:?Set HIBERMEM_CANDIDATE to qwen or phi}"
[[ "${HIBERMEM_REF}" =~ ^[0-9a-f]{40}$ ]] || { echo "An exact commit is required" >&2; exit 2; }
[[ "${HIBERMEM_CANDIDATE}" == qwen || "${HIBERMEM_CANDIDATE}" == phi ]] || { echo "Choose qwen or phi" >&2; exit 2; }
[[ -d /kaggle/working ]] || { echo "This launcher is for Kaggle" >&2; exit 2; }

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
[[ "$(git rev-parse HEAD)" == "${HIBERMEM_REF}" ]] || { echo "Commit mismatch" >&2; exit 2; }
python - <<'PY'
import pathlib
import subprocess
import tomllib

root = pathlib.Path.cwd()
assert tomllib.loads((root / "pyproject.toml").read_text())["project"]["name"] == "hibermem", "Wrong repository"
changes = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], text=True)
assert not changes.strip(), "Commit all source/config changes before inference"
PY

RUN_DIR="results/phase2r_v2/${HIBERMEM_CANDIDATE}"
ARTIFACT="/kaggle/working/hibermem-v2-${HIBERMEM_CANDIDATE}-${HIBERMEM_REF:0:12}-artifacts.tar.gz"
BASE_PYTHON="$(python -c 'import sys; print(sys.executable)')"
STAGE="environment_setup"
RESULT_VALIDATED=0
mkdir -p results/phase2r_v2
finish() {
  local raw_status="$1"
  trap - EXIT
  set +e
  "${BASE_PYTHON}" scripts/kaggle_launch_status.py --stage "${STAGE}" \
    --raw-exit "${raw_status}" --validated "${RESULT_VALIDATED}" \
    --candidate "${HIBERMEM_CANDIDATE}" --commit "${HIBERMEM_REF}" \
    --output "results/phase2r_v2/${HIBERMEM_CANDIDATE}-launcher-status.json"
  local status="$?"
  if ! tar -czf "${ARTIFACT}" results/phase2r_v2; then
    echo "Artifact packaging failed; preserve the results folder manually" >&2
    exit 2
  fi
  echo "Download: ${ARTIFACT}"
  echo "Exit ${status}: 0=validated qualification; 1=validated negative screen; 2=infrastructure error."
  echo "This is development evidence only. Confirmation and test remain locked."
  exit "${status}"
}
trap 'finish "$?"' EXIT

# Inherit Kaggle's CUDA torch. Isolate project package changes from notebook apps.
BASE_TORCH="$("${BASE_PYTHON}" -c 'import torch; print(torch.__version__)')"
# Do not reuse or delete the old, possibly partial ensurepip-based environment.
ENV_DIR="/kaggle/working/hibermem-v2-env-nopip"
ENV_PYTHON="${ENV_DIR}/bin/python"
if [[ ! -e "${ENV_DIR}" ]]; then
  "${BASE_PYTHON}" -m venv --without-pip --system-site-packages "${ENV_DIR}" \
    2>&1 | tee "results/phase2r_v2/${HIBERMEM_CANDIDATE}-bootstrap.log"
fi
[[ -x "${ENV_PYTHON}" && -f "${ENV_DIR}/pyvenv.cfg" ]] || { echo "Incomplete no-pip environment; preserve it and use a fresh Kaggle session" >&2; exit 2; }
"${ENV_PYTHON}" -c 'import pathlib, sys; assert pathlib.Path(sys.prefix) == pathlib.Path(sys.argv[1]), "Wrong environment prefix"' "${ENV_DIR}"
export HF_HOME="/kaggle/working/hf-cache-hibermem-v2-${HIBERMEM_CANDIDATE}"
export HIBERMEM_MIN_FREE_STORAGE_GIB="${HIBERMEM_MIN_FREE_STORAGE_GIB:-15}"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

STAGE="dependency_install"
# pip --python can manage an environment which has no pip/ensurepip of its own.
"${BASE_PYTHON}" -m pip --python "${ENV_PYTHON}" install \
  -r configs/requirements/kaggle-phase2r-v2.txt -e '.[dev,reference]' \
  2>&1 | tee "results/phase2r_v2/${HIBERMEM_CANDIDATE}-install.log"
STAGE="environment_check"
[[ "$("${ENV_PYTHON}" -c 'import torch; print(torch.__version__)')" == "${BASE_TORCH}" ]] || { echo "PyTorch changed unexpectedly; stop and review" >&2; exit 2; }
"${BASE_PYTHON}" -m pip --python "${ENV_PYTHON}" freeze > "results/phase2r_v2/${HIBERMEM_CANDIDATE}-packages.txt"
"${ENV_PYTHON}" scripts/verify_kaggle_environment.py --output "results/phase2r_v2/${HIBERMEM_CANDIDATE}-environment.json"
STAGE="tests"
"${ENV_PYTHON}" scripts/run_tests.py -q \
  --junitxml "results/phase2r_v2/${HIBERMEM_CANDIDATE}-tests.xml" \
  2>&1 | tee "results/phase2r_v2/${HIBERMEM_CANDIDATE}-tests.log"
STAGE="controls"
"${ENV_PYTHON}" scripts/run_phase2r_v2.py --candidate "${HIBERMEM_CANDIDATE}" \
  --controls-only --run-dir "results/phase2r_v2/${HIBERMEM_CANDIDATE}-controls"
set +e
STAGE="screen"
"${ENV_PYTHON}" -u scripts/run_phase2r_v2.py --candidate "${HIBERMEM_CANDIDATE}" \
  --run-dir "${RUN_DIR}" 2>&1 | tee "results/phase2r_v2/${HIBERMEM_CANDIDATE}.log"
SCREEN_EXIT="${PIPESTATUS[0]}"
set -e
if [[ "${SCREEN_EXIT}" != 0 && "${SCREEN_EXIT}" != 1 ]]; then
  exit "${SCREEN_EXIT}"
fi
set +e
STAGE="artifact_validation"
"${ENV_PYTHON}" scripts/validate_phase2r_v2_report.py --report "${RUN_DIR}/report.json"
VALIDATION_EXIT="$?"
set -e
[[ "${VALIDATION_EXIT}" == "${SCREEN_EXIT}" ]] || { echo "Artifact validation disagrees with the run" >&2; exit 2; }
RESULT_VALIDATED=1
STAGE="complete"
exit "${SCREEN_EXIT}"
