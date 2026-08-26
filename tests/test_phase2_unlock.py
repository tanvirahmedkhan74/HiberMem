import hashlib
import json

import pytest

from hibermem.experiments.phase2 import unlock_phase2_test


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_test_unlock_requires_p2a_and_freezes_discovery_and_validation(tmp_path) -> None:
    config = {"phase": 2, "seed": 1}
    validation = {
        "config_sha256": _hash(config),
        "summary": {"ready_for_test_unlock": True},
    }
    discovery = {"p2a_candidate_gate": {"passed": False}}
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (tmp_path / "validation.json").write_text(json.dumps(validation), encoding="utf-8")
    (tmp_path / "discovery.json").write_text(json.dumps(discovery), encoding="utf-8")

    with pytest.raises(RuntimeError, match="P2-A"):
        unlock_phase2_test(run_dir=tmp_path)

    discovery["p2a_candidate_gate"]["passed"] = True
    (tmp_path / "discovery.json").write_text(json.dumps(discovery), encoding="utf-8")
    unlock = unlock_phase2_test(run_dir=tmp_path)
    assert unlock["decision"] == "test_unlocked"
    assert unlock["discovery_artifact_hash"] == _hash(discovery)
    assert unlock["validation_artifact_hash"] == _hash(validation)
