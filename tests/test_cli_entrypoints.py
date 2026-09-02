import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("script", ["run_phase2r_v2.py", "validate_phase2r_v2_report.py",
                                     "analyze_phase2_public.py", "freeze_phase2r_confirmation.py",
                                     "run_exact_mechanism.py", "validate_exact_mechanism.py",
                                     "analyze_phase2r_v2_interactions.py",
                                     "run_e3c_contract.py", "validate_e3c_report.py",
                                     "run_e4_prospective.py", "validate_e4_report.py",
                                     "freeze_e4_protocol.py"])
def test_entrypoint_runs_without_repository_root_on_import_path(tmp_path, script):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / script), "--help"],
                            cwd=tmp_path, env=environment, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
