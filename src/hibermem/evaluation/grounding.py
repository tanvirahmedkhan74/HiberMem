"""Independent E3d grounding-decomposition summaries and readiness checks."""

from __future__ import annotations

from collections import defaultdict
from statistics import fmean

from .factorial import outcome_breakdown


def _rate(rows: list[dict], key: str) -> float:
    if not rows:
        raise ValueError(f"cannot compute {key} on an empty E3d subgroup")
    return fmean(bool(row[key]) for row in rows)


def _decode_summary(rows: list[dict], budget: int, arm: str) -> dict[str, float | int]:
    strict_key = "certificate_valid" if arm == "structured_verifier_v1" else "strict_format"
    return {
        "n": len(rows),
        "strict_format_rate": _rate(rows, strict_key),
        "at_generation_limit_rate": fmean(
            int(row["output_tokens"]) >= budget for row in rows
        ),
        "parse_null_rate": _rate(rows, "parse_null"),
        "mean_input_tokens": fmean(int(row["input_tokens"]) for row in rows),
        "mean_output_tokens": fmean(int(row["output_tokens"]) for row in rows),
        "mean_latency_seconds": fmean(float(row["latency_seconds"]) for row in rows),
    }


def _single_dual(rows: list[dict]) -> dict[str, object]:
    paired: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        if row["supported"]:
            paired[row["pairing_key"]][row["ledger_mode"]] = row
    missing = [key for key, value in paired.items() if set(value) != {"single_path", "dual_path"}]
    if missing:
        raise ValueError("E3d supported single/dual pairing is incomplete")
    differences = [
        value["single_path"]["reward"] - value["dual_path"]["reward"]
        for value in paired.values()
    ]
    return {
        "n_pairs": len(differences),
        "supported_accuracy_drop": fmean(differences),
        "single_better": sum(value > 0 for value in differences),
        "dual_better": sum(value < 0 for value in differences),
        "ties": sum(value == 0 for value in differences),
    }


def _per_link(rows: list[dict]) -> dict[str, dict[str, float | int]]:
    grouped: dict[tuple[str, str, int], list[dict]] = defaultdict(list)
    for row in rows:
        if row["evidence_kind"] in ("missing_exact_link", "missing_full_link"):
            grouped[(row["family"], row["evidence_kind"], row["missing_link_position"])].append(row)
    return {
        f"{family}:{kind}:{position}": {
            "n": len(group),
            "unsupported_assertion": _rate(group, "unsupported_assertion"),
        }
        for (family, kind, position), group in sorted(grouped.items())
    }


def _readiness(
    *, arm: str, family_summaries: dict[str, dict], decoding: dict,
    counterfactual: dict, other_query: dict, per_link: dict,
    single_dual: dict, thresholds: dict,
) -> dict[str, object]:
    checks: dict[str, bool] = {}
    for family, summary in family_summaries.items():
        checks[f"{family}.supported_accuracy"] = (
            summary["outcomes"]["supported_accuracy"] is not None
            and summary["outcomes"]["supported_accuracy"]
            >= thresholds["min_supported_accuracy"]
        )
        checks[f"{family}.unsupported_assertion"] = (
            summary["outcomes"]["unsupported_assertion"] is not None
            and summary["outcomes"]["unsupported_assertion"]
            <= thresholds["max_unsupported_assertion"]
        )
        checks[f"{family}.full_accuracy"] = (
            summary["full"]["accuracy"] >= thresholds["min_full_accuracy"]
        )
        checks[f"{family}.exact_support_accuracy"] = (
            summary["exact_support"]["accuracy"]
            >= thresholds["min_exact_support_accuracy"]
        )
    checks.update(
        {
            "global.strict_format": decoding["strict_format_rate"]
            >= thresholds["min_strict_format_rate"],
            "global.generation_limit": decoding["at_generation_limit_rate"]
            <= thresholds["max_generation_limit_rate"],
            "global.counterfactual_tracking": counterfactual["tracking_accuracy"]
            >= thresholds["min_counterfactual_tracking"],
            "global.stale_base_capture": counterfactual["stale_base_capture_rate"]
            <= thresholds["max_stale_base_capture"],
            "global.other_query_capture": other_query["capture_rate"]
            <= thresholds["max_other_query_capture"],
            "global.single_to_dual_drop": single_dual["supported_accuracy_drop"]
            <= thresholds["max_single_to_dual_drop"],
        }
    )
    for group, values in per_link.items():
        checks[f"per_link.{group}"] = (
            values["unsupported_assertion"]
            <= thresholds["max_per_link_unsupported_assertion"]
        )
    passed = all(checks.values())
    return {
        "passed": passed,
        "checks": checks,
        "failed_checks": sorted(key for key, value in checks.items() if not value),
        "label_only_readiness_passed": arm == "query_anchored_v1" and passed,
        "structured_verifier_e4_eligible": False,
    }


def summarize_grounding(rows: list[dict], suite, config: dict) -> dict[str, object]:
    expected = {case["case_id"] for case in suite.conditions()}
    if len(rows) != len(expected) or {row["case_id"] for row in rows} != expected:
        raise ValueError("E3d analysis requires every unique planned condition")
    if any(row["split"] != "discovery" for row in rows):
        raise ValueError("E3d may not contain future or historical-test rows")
    budget = int(config["generation"]["max_new_tokens"])
    thresholds = config["readiness"]
    arms: dict[str, dict[str, object]] = {}
    readiness: dict[str, dict[str, object]] = {}
    for arm in suite.arms:
        arm_rows = [row for row in rows if row["arm"] == arm]
        families: dict[str, dict[str, object]] = {}
        for family in config["families"]:
            family_rows = [row for row in arm_rows if row["family"] == family]
            families[family] = {
                "outcomes": outcome_breakdown(family_rows),
                "full": outcome_breakdown(
                    [row for row in family_rows if row["evidence_kind"] == "full"]
                ),
                "exact_support": outcome_breakdown(
                    [
                        row
                        for row in family_rows
                        if row["evidence_kind"] == "exact_support"
                    ]
                ),
            }
        counterfactual_rows = [
            row
            for row in arm_rows
            if row["world"] == "counterfactual"
            and row["evidence_kind"] in ("exact_support", "full")
        ]
        counterfactual = {
            "n": len(counterfactual_rows),
            "tracking_accuracy": fmean(row["reward"] for row in counterfactual_rows),
            "stale_base_capture_rate": fmean(
                row["parsed_action"] == row["stale_base_destination"]
                and row["target_destination"] != row["stale_base_destination"]
                for row in counterfactual_rows
            ),
        }
        dual_rows = [row for row in arm_rows if row["ledger_mode"] == "dual_path"]
        other_query = {
            "n": len(dual_rows),
            "capture_rate": fmean(
                row["parsed_action"] == row["other_query_destination"]
                for row in dual_rows
            ),
        }
        per_link = _per_link(arm_rows)
        single_dual = _single_dual(arm_rows)
        decoding = _decode_summary(arm_rows, budget, arm)
        arms[arm] = {
            "n_conditions": len(arm_rows),
            "families": families,
            "decoding": decoding,
            "counterfactual": counterfactual,
            "other_query": other_query,
            "per_link": per_link,
            "single_to_dual": single_dual,
            "bank_level": {
                str(bank_seed): outcome_breakdown(
                    [row for row in arm_rows if row["base_bank_seed"] == bank_seed]
                )
                for bank_seed in suite.base_bank_seeds
            },
        }
        readiness[arm] = _readiness(
            arm=arm,
            family_summaries=families,
            decoding=decoding,
            counterfactual=counterfactual,
            other_query=other_query,
            per_link=per_link,
            single_dual=single_dual,
            thresholds=thresholds,
        )
    a1_passed = readiness["query_anchored_v1"]["passed"]
    return {
        "scope": "E3d measurement-instrument qualification; no retention result",
        "stage": suite.stage,
        "arms": arms,
        "readiness": readiness,
        "query_anchored_passed": a1_passed,
        "verification_config_eligible": None,
        "e4_design_eligible": None,
        "eligibility_note": (
            "readiness metrics alone never grant capability; the experiment layer must "
            "also verify real/mock status, immutable source evidence, and stage"
        ),
        "automatic_selection": None,
        "independent_base_banks": len(suite.base_bank_seeds),
        "query_rows_treated_as_independent": False,
        "future_queries_evaluated": 0,
        "historical_test_access": False,
        "structured_verifier_e4_eligible": False,
    }


__all__ = ["summarize_grounding"]
