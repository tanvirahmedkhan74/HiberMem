import json

import pytest

from scripts.freeze_phase2r_confirmation import freeze_config


def test_freeze_rejects_unsupported_legacy_selection(tmp_path) -> None:
    revision = "a" * 40
    screen_path = tmp_path / "screen.json"
    screen_path.write_text(
        json.dumps(
            {
                "selected_candidate": {
                    "model_label": "candidate",
                    "backend": {
                        "type": "hf_local",
                        "model_id": "organization/model",
                        "model_revision": revision,
                        "device": "cuda",
                        "dtype": "float16",
                        "quantization": "none",
                    },
                    "selection_rule": "locked rule",
                }
            }
        ),
        encoding="utf-8",
    )
    base_path = tmp_path / "base.json"
    base_path.write_text(
        json.dumps({"phase": 2, "gate_thresholds": {"p2a": {}, "p2b": {}}}),
        encoding="utf-8",
    )
    output = tmp_path / "confirmation.json"

    with pytest.raises(RuntimeError, match="legacy v1 confirmation"):
        freeze_config(screen_report_path=screen_path, base_config_path=base_path, output_path=output)
    assert not output.exists()

    output.write_text("preserve me", encoding="utf-8")
    with pytest.raises(FileExistsError):
        freeze_config(
            screen_report_path=screen_path,
            base_config_path=base_path,
            output_path=output,
        )


def test_freeze_rejects_screen_without_qualified_selection(tmp_path) -> None:
    screen_path = tmp_path / "screen.json"
    screen_path.write_text('{"selected_candidate": null}', encoding="utf-8")
    base_path = tmp_path / "base.json"
    base_path.write_text('{"phase": 2}', encoding="utf-8")

    with pytest.raises(RuntimeError, match="did not select"):
        freeze_config(
            screen_report_path=screen_path,
            base_config_path=base_path,
            output_path=tmp_path / "confirmation.json",
        )
