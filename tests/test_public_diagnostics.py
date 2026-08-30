import json

import pytest

from hibermem.coalition.masks import index_to_mask, serialize_mask
from scripts.analyze_phase2_public import analyze


def test_public_analyzer_uses_only_discovery_and_validation(tmp_path):
    masks = [index_to_mask(index, 8) for index in range(256)]
    values = [.1 * mask[0] + .8 * mask[0] * mask[1] for mask in masks]
    discovery = {"stage": "discovery", "bank_results": [{
        "bank_id": "bank-a", "coalition_masks": [serialize_mask(m) for m in masks],
        "coalition_values": values}]}
    records = [{"bank_id": bank, "split": "validation", "actual_deletion_ratio": .75,
                "policy": policy, "accuracy": accuracy}
               for bank in ("bank-a", "bank-b") for policy, accuracy in (("interaction", .9), ("item", .1))]
    (tmp_path / "discovery.json").write_text(json.dumps(discovery))
    (tmp_path / "validation.json").write_text(json.dumps({"stage": "validation", "retention_records": records}))
    # Deliberately invalid: any attempt to read test would fail JSON parsing.
    (tmp_path / "test.json").write_text("DO NOT READ")
    result = analyze(tmp_path)
    assert result["bank_fits"][0]["exact_shapley_items"][0] == pytest.approx(.5)
    assert result["bank_fits"][0]["predictive_metrics"]["2"]["r2"] == pytest.approx(1)
    assert result["severe_validation_interval"]["mean"] == pytest.approx(.8)
    records[0]["split"] = "test"
    (tmp_path / "validation.json").write_text(json.dumps({"stage": "validation", "retention_records": records}))
    with pytest.raises(ValueError, match="non-validation"):
        analyze(tmp_path)
