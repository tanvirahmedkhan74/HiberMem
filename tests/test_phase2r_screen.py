import json

from scripts.run_phase2r_screen import run_screen


def test_phase2r_screen_uses_fresh_public_banks_and_never_test_split(tmp_path) -> None:
    config = {
        "phase": "2-R",
        "scientific_gate_eligible": False,
        "seed": 2718,
        "calibration": {"n_banks": 2, "bank_start": 100},
        "generation": {"do_sample": False, "max_new_tokens": 8},
        "qualification_thresholds": {
            "full_direct_accuracy_min": 0.9,
            "full_two_hop_accuracy_min": 0.8,
            "memory_gap_min": 0.5,
            "full_parse_rate_min": 0.98,
            "missing_link_false_positive_rate_max": 0.25,
            "passing_bank_fraction_min": 0.8,
        },
        "candidates": [
            {
                "label": "mock",
                "backend": {
                    "type": "mock",
                    "model_id": "hibermem/mock-controlled-v1",
                    "model_revision": "1",
                    "quantization": "none",
                },
            }
        ],
    }
    run_dir = tmp_path / "results" / "screen"

    report = run_screen(root=tmp_path, config=config, run_dir=run_dir)

    assert report["selected_candidate"]["model_label"] == "mock"
    assert report["calibration"] == {"n_banks": 2, "bank_start": 100}
    evaluations = json.loads(
        (run_dir / "hibermem-mock-controlled-v1" / "evaluations.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(evaluations) == 276
    assert {row["split"] for row in evaluations} == {"discovery", "validation"}
    assert {row["bank_id"] for row in evaluations} == {"bank-100", "bank-101"}
