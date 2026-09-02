"""Read-only summaries for the E3c output-contract diagnostic."""

from __future__ import annotations

from collections import defaultdict
from statistics import fmean

from .factorial import outcome_breakdown


def _decode_summary(rows: list[dict], budget: int) -> dict[str, float | int]:
    if not rows:
        raise ValueError("contract decode summary requires rows")
    return {
        "n": len(rows),
        "strict_format_rate": fmean(bool(row["strict_format"]) for row in rows),
        "at_generation_limit_rate": fmean(
            int(row["output_tokens"]) >= budget for row in rows
        ),
        "parse_null_rate": fmean(bool(row["parse_null"]) for row in rows),
        "mean_output_tokens": fmean(int(row["output_tokens"]) for row in rows),
    }


def summarize_contract(
    rows: list[dict], suite, config: dict
) -> dict[str, object]:
    expected = {case["case_id"] for case in suite.conditions()}
    if len(rows) != len(expected) or {row["case_id"] for row in rows} != expected:
        raise ValueError("contract analysis requires every unique planned condition")
    if any(row["split"] != "discovery" for row in rows):
        raise ValueError("E3c may contain development discovery rows only")

    family_by_bank = {
        bank_id: metadata["family"]
        for bank_id, metadata in suite.base.game_metadata.items()
    }
    budget = int(config["generation"]["max_new_tokens"])
    by_contract: dict[str, dict[str, object]] = {}
    thresholds = config["readiness"]
    readiness: dict[str, dict[str, object]] = {}
    for contract in suite.contracts:
        contract_rows = [row for row in rows if row["contract"] == contract]
        families = {}
        family_checks: list[bool] = []
        for family in config["families"]:
            rr = [row for row in contract_rows if family_by_bank[row["bank_id"]] == family]
            outcomes = outcome_breakdown(rr)
            decode = _decode_summary(rr, budget)
            full = outcome_breakdown([row for row in rr if row["mask_index"] == 255])
            checks = {
                "supported_accuracy": (
                    outcomes["supported_accuracy"] is not None
                    and outcomes["supported_accuracy"]
                    >= thresholds["min_supported_accuracy"]
                ),
                "unsupported_assertion": (
                    outcomes["unsupported_assertion"] is not None
                    and outcomes["unsupported_assertion"]
                    <= thresholds["max_unsupported_assertion"]
                ),
            }
            family_checks.extend(checks.values())
            families[family] = {
                "outcomes": outcomes,
                "full_outcomes": full,
                "decoding": decode,
                "checks": checks,
            }
        decoding = _decode_summary(contract_rows, budget)
        global_checks = {
            "strict_format": (
                decoding["strict_format_rate"] >= thresholds["min_strict_format_rate"]
            ),
            "generation_limit": (
                decoding["at_generation_limit_rate"]
                <= thresholds["max_generation_limit_rate"]
            ),
        }
        passed = all(family_checks) and all(global_checks.values())
        by_contract[contract] = {
            "n_conditions": len(contract_rows),
            "families": families,
            "decoding": decoding,
        }
        readiness[contract] = {
            "passed": passed,
            "family_checks": {
                family: families[family]["checks"] for family in config["families"]
            },
            "global_checks": global_checks,
        }

    keyed: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        paired_id = row["case_id"].split(":", 1)[1]
        keyed[paired_id][row["contract"]] = row
    if any(set(pair) != set(suite.contracts) for pair in keyed.values()):
        raise ValueError("contract comparison lost a paired condition")
    reference = suite.contracts[0]
    paired = {}
    for contract in suite.contracts[1:]:
        pairs = [(pair[reference], pair[contract]) for pair in keyed.values()]
        paired[contract] = {
            "reference": reference,
            "n_pairs": len(pairs),
            "accuracy_delta": fmean(b["reward"] - a["reward"] for a, b in pairs),
            "strict_format_delta": fmean(
                int(b["strict_format"]) - int(a["strict_format"]) for a, b in pairs
            ),
            "unsupported_assertion_delta": fmean(
                int(b["unsupported_assertion"]) - int(a["unsupported_assertion"])
                for a, b in pairs
            ),
            "wrong_to_correct": sum(not a["reward"] and b["reward"] for a, b in pairs),
            "correct_to_wrong": sum(a["reward"] and not b["reward"] for a, b in pairs),
        }

    passing = [name for name, result in readiness.items() if result["passed"]]
    return {
        "scope": "fresh development-only output-contract diagnostic",
        "contracts": by_contract,
        "readiness": readiness,
        "passing_contracts": passing,
        "automatic_selection": None,
        "selection_note": (
            "a passing contract must be explicitly frozen; no retention outcome was used"
        ),
        "paired_changes_from_first_contract": paired,
        "independent_base_banks": suite.manifest()["independent_base_banks"],
        "future_queries_evaluated": 0,
        "qualified": None,
        "test_access": False,
    }


__all__ = ["summarize_contract"]
