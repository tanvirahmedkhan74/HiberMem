#!/usr/bin/env bash
set -euo pipefail

: "${HIBERMEM_REPO_URL:?Set HIBERMEM_REPO_URL to the GitHub repository containing HiberMem}"
: "${HIBERMEM_REF:?Set HIBERMEM_REF to the exact 40-character confirmation commit}"
if [[ ! "${HIBERMEM_REF}" =~ ^[0-9a-f]{40}$ ]]; then
  echo "HIBERMEM_REF must be an exact 40-character Git commit, not a branch" >&2
  exit 2
fi

WORKDIR="/kaggle/working/hibermem-confirmation"
RUN_DIR="results/phase2r_kaggle_confirmation/kaggle"
ARTIFACT="/kaggle/working/hibermem-phase2r-confirmation-artifacts.tar.gz"

if [[ -e "${WORKDIR}" && ! -d "${WORKDIR}/.git" ]]; then
  echo "Refusing to overwrite non-Git path ${WORKDIR}" >&2
  exit 2
fi
if [[ ! -d "${WORKDIR}/.git" ]]; then
  git clone --filter=blob:none --no-checkout "${HIBERMEM_REPO_URL}" "${WORKDIR}"
fi
git -C "${WORKDIR}" fetch --depth 1 origin "${HIBERMEM_REF}"
git -C "${WORKDIR}" checkout --detach FETCH_HEAD
ACTUAL_REF="$(git -C "${WORKDIR}" rev-parse HEAD)"
if [[ "${ACTUAL_REF}" != "${HIBERMEM_REF}" ]]; then
  echo "Checked out ${ACTUAL_REF}, expected ${HIBERMEM_REF}" >&2
  exit 2
fi

cd "${WORKDIR}"
python - <<'PY'
import pathlib
import tomllib

project = tomllib.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8"))
if project["project"]["name"] != "hibermem":
    raise SystemExit("Wrong repository: expected the HiberMem project")
if not pathlib.Path("configs/experiments/phase2r_kaggle_confirmation.json").exists():
    raise SystemExit("Frozen confirmation config is absent from this commit")
PY

export HF_HOME="/kaggle/working/hf-cache-confirmation"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r configs/requirements/kaggle-phase2r.txt
python -m pip install --quiet -e ".[dev,reference]"
python scripts/verify_kaggle_environment.py \
  --output results/phase2r_kaggle_confirmation/environment.json
python -m pytest -q

set +e
python scripts/run_phase2.py \
  --stage discovery-validation \
  --config configs/experiments/phase2r_kaggle_confirmation.json \
  --run-dir "${RUN_DIR}"
RUN_EXIT=$?
set -e

tar -czf "${ARTIFACT}" "${RUN_DIR}"
echo "Download this Kaggle output artifact: ${ARTIFACT}"
echo "The held-out test is still locked; review report.json before any unlock."
exit "${RUN_EXIT}"
