"""Raw calibration records and inexpensive prompt-reading controls."""

from __future__ import annotations

import hashlib
import re

from hibermem.backends import MockBackend
from hibermem.environments.controlled.prompts import build_messages
from .scoring import parse_action
from .qualification import summarize_v2


def calibration_row(case, view, raw: str, parsed: str | None) -> dict:
    return {
        "case_id": case.case_id, "base_bank_id": case.base_bank_id,
        "query_id": case.query.query_id, "split": case.query.split.value,
        "condition": case.condition, "kind": case.kind, "supported": case.supported,
        "counterfactual_id": case.counterfactual_id, "world": case.world,
        "reward": view.score(case.query, parsed), "parsed_action": parsed,
        "abstained": parsed == "UNKNOWN", "parse_null": parsed is None,
        "unsupported_assertion": not case.supported and parsed not in (None, "UNKNOWN"),
        "strict_format": parsed is not None and raw.strip() == parsed,
        "raw_output": raw,
        "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
    }


def control_results(suite, thresholds: dict) -> dict:
    """Require the prompt-reading oracle to qualify and answer-copy controls to fail."""
    result = {}
    for name in ("symbolic_oracle", "destination_copy", "first_option"):
        rows = []
        oracle = MockBackend()
        for case in suite.cases:
            bank = suite.dataset.bank(case.query.bank_id)
            memories = tuple(m for m, keep in zip(bank.memories, case.mask) if keep)
            if name == "symbolic_oracle":
                raw = oracle.generate(build_messages(memories, case.query)).text
            elif name == "destination_copy":
                labels = re.findall(r"DS[0-9]+", " ".join(m.text for m in memories))
                raw = labels[0] if labels else "UNKNOWN"
            else:
                raw = case.query.options[0]
            rows.append(calibration_row(case, suite.dataset.view(case.query.split), raw, parse_action(raw, case.query.options)))
        result[name] = summarize_v2(rows, thresholds)
    if not result["symbolic_oracle"]["qualified"] or any(
        result[name]["qualified"] for name in ("destination_copy", "first_option")
    ):
        raise RuntimeError("benchmark control validation failed; refusing model inference")
    return result
