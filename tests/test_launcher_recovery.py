from pathlib import Path
import sys

import pytest

from scripts.kaggle_launch_status import classify_exit
from scripts.run_tests import test_command as build_test_command


@pytest.mark.parametrize("stage", ["environment_setup", "dependency_install", "tests", "screen", "artifact_validation"])
def test_exit_one_before_validated_completion_is_not_a_negative_model_result(stage):
    result = classify_exit(stage, 1, False)
    assert result["exit_code"] == 2
    assert result["outcome"] == "infrastructure_error"


@pytest.mark.parametrize("code,outcome", [(0, "development_qualified"), (1, "development_negative")])
def test_only_validated_completion_reports_model_result(code, outcome):
    assert classify_exit("complete", code, True)["outcome"] == outcome
    assert classify_exit("complete", code, True)["exit_code"] == code
    assert classify_exit("complete", code, False)["exit_code"] == 2


def test_test_runner_uses_current_interpreter_and_unique_workspace_scratch(tmp_path):
    first = build_test_command(tmp_path, ["-q"])
    second = build_test_command(tmp_path, ["-q"])
    assert first[0] == sys.executable
    assert first[1:4] == ["-m", "pytest", "--basetemp"]
    assert first[4] != second[4]
    assert Path(first[4]).is_relative_to(tmp_path / "results" / "pytest-runs")
    assert Path(first[4]).exists()
    with pytest.raises(ValueError, match="fresh basetemp"):
        build_test_command(tmp_path, ["--basetemp", str(tmp_path)])


def test_kaggle_launcher_bypasses_ensurepip_and_targets_the_environment():
    script = (Path(__file__).resolve().parents[1] / "kaggle/run_phase2r_v2.sh").read_text()
    assert "-m venv --without-pip --system-site-packages" in script
    assert '-m pip --python "${ENV_PYTHON}" install' in script
    assert "scripts/run_tests.py" in script
    assert '--junitxml "results/phase2r_v2/${HIBERMEM_CANDIDATE}-tests.xml"' in script
    assert 'tee "results/phase2r_v2/${HIBERMEM_CANDIDATE}-tests.log"' in script


def test_exact_launcher_has_no_scientific_success_or_test_path():
    script = (Path(__file__).resolve().parents[1] / "kaggle/run_exact_mechanism.sh").read_text()
    assert "-m venv --without-pip --system-site-packages" in script
    assert '-m pip --python "${ENV_PYTHON}" install' in script
    assert "scripts/run_tests.py" in script and "scripts/validate_exact_mechanism.py" in script
    assert '"qualified": None' in script
    assert "0=validated completed diagnostic" in script
    assert "freeze_phase2r" not in script and "--stage unlock" not in script
