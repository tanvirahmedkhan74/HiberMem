#!/usr/bin/env bash
set -euo pipefail

: "${HIBERMEM_REPO_URL:?Set HIBERMEM_REPO_URL to the GitHub repository containing this HiberMem project}"
HIBERMEM_REF="${HIBERMEM_REF:-main}"
WORKDIR="/kaggle/working/hibermem"
ARTIFACT="/kaggle/working/hibermem-phase2r-screen-artifacts.tar.gz"

if [[ -e "${WORKDIR}" && ! -d "${WORKDIR}/.git" ]]; then
  echo "Refusing to overwrite non-Git path ${WORKDIR}" >&2
  exit 2
fi

if [[ ! -d "${WORKDIR}/.git" ]]; then
  git clone --filter=blob:none --no-checkout "${HIBERMEM_REPO_URL}" "${WORKDIR}"
fi
git -C "${WORKDIR}" fetch --depth 1 origin "${HIBERMEM_REF}"
git -C "${WORKDIR}" checkout --detach FETCH_HEAD

python - "${WORKDIR}" <<'PY'
import pathlib
import sys
import tomllib

root = pathlib.Path(sys.argv[1])
pyproject = root / "pyproject.toml"
if not pyproject.exists():
    raise SystemExit("Wrong repository: pyproject.toml is missing")
name = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["name"]
if name != "hibermem":
    raise SystemExit(
        f"Wrong repository: expected pyproject project 'hibermem', found {name!r}"
    )
PY

cd "${WORKDIR}"
export HF_HOME="/kaggle/working/hf-cache"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r configs/requirements/kaggle-phase2r.txt
python -m pip install --quiet -e ".[dev,reference]"

python scripts/verify_kaggle_environment.py
python -m pytest -q

set +e
python scripts/run_phase2r_screen.py \
  --config configs/experiments/phase2r_kaggle_screen.json \
  --run-dir results/phase2r_kaggle_screen/kaggle
SCREEN_EXIT=$?
set -e

tar -czf "${ARTIFACT}" \
  results/phase2r_kaggle_environment.json \
  results/phase2r_kaggle_screen/kaggle
echo "Download this Kaggle output artifact: ${ARTIFACT}"
exit "${SCREEN_EXIT}"
