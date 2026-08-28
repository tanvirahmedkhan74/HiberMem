import json
import sys

import scripts.run_phase2 as run_phase2


def test_failed_validation_does_not_suggest_test_unlock(
    tmp_path, monkeypatch, capsys
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({}), encoding="utf-8")
    run_dir = tmp_path / "run"

    monkeypatch.setattr(run_phase2, "_require_phase1", lambda: None)
    monkeypatch.setattr(run_phase2, "_latest", lambda _path: None)
    monkeypatch.setattr(
        run_phase2,
        "create_phase2_run",
        lambda **_kwargs: {"validation": {"ready_for_test_unlock": False}},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_phase2.py",
            "--config",
            str(config_path),
            "--run-dir",
            str(run_dir),
        ],
    )

    assert run_phase2.main() == 1
    output = capsys.readouterr().out
    assert "Test remains locked" in output
    assert "Resume with --stage unlock" not in output


def test_phase1_tracked_certificate_supports_clean_remote_clone(
    tmp_path, monkeypatch
) -> None:
    missing_report = tmp_path / "results" / "phase1_report.json"
    certificate = tmp_path / "configs" / "gates" / "phase1_pass.json"
    certificate.parent.mkdir(parents=True)
    certificate.write_text(
        json.dumps({"phase": 1, "gate": "P1", "gate_passed": True}),
        encoding="utf-8",
    )
    monkeypatch.setattr(run_phase2, "PHASE1_REPORT", missing_report)
    monkeypatch.setattr(run_phase2, "PHASE1_CERTIFICATE", certificate)

    run_phase2._require_phase1()
