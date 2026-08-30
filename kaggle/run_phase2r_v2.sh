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
mkdir -p results/phase2r_v2
finish() {
  local status="$1"
  set +e
  if ! tar -czf "${ARTIFACT}" results/phase2r_v2; then
    echo "Artifact packaging failed; preserve the results folder manually" >&2
    exit 2
  fi
  echo "Download: ${ARTIFACT}"
  echo "Exit ${status}: 0=screen qualified; 1=negative screen; 2=runner/setup error. Other codes may be dependency/test failures."
  echo "This is development evidence only. Confirmation and test remain locked."
  exit "${status}"
}
trap 'finish "$?"' EXIT

# Inherit Kaggle's CUDA torch. Isolate project package changes from notebook apps.
BASE_TORCH="$(python -c 'import torch; print(torch.__version__)')"
ENV_DIR="/kaggle/working/hibermem-v2-env"
if [[ ! -d "${ENV_DIR}" ]]; then
  python -m venv --system-site-packages "${ENV_DIR}"
fi
[[ -f "${ENV_DIR}/bin/activate" ]] || { echo "Invalid environment path" >&2; exit 2; }
source "${ENV_DIR}/bin/activate"
export HF_HOME="/kaggle/working/hf-cache-hibermem-v2-${HIBERMEM_CANDIDATE}"
export HIBERMEM_MIN_FREE_STORAGE_GIB="${HIBERMEM_MIN_FREE_STORAGE_GIB:-15}"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

python -m pip install -r configs/requirements/kaggle-phase2r-v2.txt -e '.[dev,reference]'
[[ "$(python -c 'import torch; print(torch.__version__)')" == "${BASE_TORCH}" ]] || { echo "PyTorch changed unexpectedly; stop and review" >&2; exit 2; }
python -m pip freeze > "results/phase2r_v2/${HIBERMEM_CANDIDATE}-packages.txt"
python scripts/verify_kaggle_environment.py --output "results/phase2r_v2/${HIBERMEM_CANDIDATE}-environment.json"
python -m pytest -q
python scripts/run_phase2r_v2.py --candidate "${HIBERMEM_CANDIDATE}" \
  --controls-only --run-dir "results/phase2r_v2/${HIBERMEM_CANDIDATE}-controls"
set +e
python -u scripts/run_phase2r_v2.py --candidate "${HIBERMEM_CANDIDATE}" \
  --run-dir "${RUN_DIR}" 2>&1 | tee "results/phase2r_v2/${HIBERMEM_CANDIDATE}.log"
SCREEN_EXIT="${PIPESTATUS[0]}"
set -e
if [[ "${SCREEN_EXIT}" != 0 && "${SCREEN_EXIT}" != 1 ]]; then
  exit "${SCREEN_EXIT}"
fi
set +e
python scripts/validate_phase2r_v2_report.py --report "${RUN_DIR}/report.json"
VALIDATION_EXIT="$?"
set -e
[[ "${VALIDATION_EXIT}" == "${SCREEN_EXIT}" ]] || { echo "Artifact validation disagrees with the run" >&2; exit 2; }
exit "${SCREEN_EXIT}"
