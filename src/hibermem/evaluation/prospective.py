"""Past-only policy freezing and future-only E4 analysis."""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
from dataclasses import dataclass
from statistics import fmean

from scipy.stats import spearmanr

from hibermem.coalition.masks import index_to_mask, mask_to_index
from hibermem.environments.controlled.prospective import PastQueryCapability
from hibermem.retention.costs import (
    equal_length_bank_audit,
    retained_payload_cost,
    validate_equal_cardinality_costs,
)
from hibermem.retention.policies import interaction_aware_mask, item_value_mask

from .factorial import outcome_breakdown
from .mechanism import analyze_game
from .predictive import paired_bank_interval, prediction_metrics
from .survival import normalized_memory_retention


def _json_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class PastEvidence:
    """Policy-safe view of past rows: no support labels, outputs, or future data."""

    records: tuple[tuple[str, str, int, float], ...]
    sha256: str

    @classmethod
    def from_rows(
        cls, rows: list[dict], capability: PastQueryCapability
    ) -> "PastEvidence":
        if not isinstance(capability, PastQueryCapability):
            raise TypeError("policy fitting requires PastQueryCapability")
        allowed_queries = {query.query_id: query for query in capability.queries}
        records = []
        seen = set()
        for row in rows:
            key = (row.get("query_id"), row.get("mask_index"))
            if key in seen:
                raise ValueError("duplicate past coalition row")
            seen.add(key)
            query = allowed_queries.get(row.get("query_id"))
            if query is None or row.get("split") != "past" or row.get("bank_id") != query.bank_id:
                raise PermissionError("non-past evidence reached policy fitting")
            reward = row.get("reward")
            mask_index = row.get("mask_index")
            if type(mask_index) is not int or not 0 <= mask_index < 256:
                raise ValueError("invalid past coalition index")
            if not isinstance(reward, (int, float)) or not math.isfinite(float(reward)):
                raise ValueError("invalid past reward")
            records.append((query.bank_id, query.query_id, mask_index, float(reward)))
        expected = len(allowed_queries) * 256
        if len(records) != expected:
            raise ValueError("policy fitting requires complete past games")
        safe = tuple(sorted(records))
        return cls(records=safe, sha256=_json_hash(safe))

    def table_by_bank(self) -> dict[str, tuple[float, ...]]:
        grouped: dict[str, dict[int, list[float]]] = {}
        for bank_id, _, mask_index, reward in self.records:
            grouped.setdefault(bank_id, {}).setdefault(mask_index, []).append(reward)
        tables = {}
        for bank_id, masks in grouped.items():
            if set(masks) != set(range(256)):
                raise ValueError("incomplete bank table in PastEvidence")
            tables[bank_id] = tuple(fmean(masks[index]) for index in range(256))
        return tables


def _coefficient_map(rows: list[dict]) -> dict[tuple[int, ...], float]:
    return {tuple(row["players"]): float(row["value"]) for row in rows}


def _predict(coefficients: dict[tuple[int, ...], float], indices: list[int]) -> list[float]:
    return [
        sum(
            value
            for term, value in coefficients.items()
            if all(index & (1 << player) for player in term)
        )
        for index in indices
    ]


def _query_overlap_weights(bank, past_queries) -> dict[int, float]:
    query_tokens = re.findall(
        r"[A-Z]+\d+", " ".join(query.text for query in past_queries)
    )
    return {
        player: float(
            sum(token in memory.text for token in query_tokens)
        )
        for player, memory in enumerate(bank.memories)
    }


def _lexical_centrality_weights(bank) -> dict[int, float]:
    tokens = [set(re.findall(r"[a-z0-9]+", memory.text.lower())) for memory in bank.memories]
    result = {}
    for player, source in enumerate(tokens):
        similarities = [
            len(source & target) / len(source | target)
            for other, target in enumerate(tokens)
            if other != player
        ]
        result[player] = fmean(similarities)
    return result


def _canonical_interaction_mask(coefficients, keep_count: int):
    rounded = {term: round(float(value), 12) for term, value in coefficients.items()}
    return interaction_aware_mask(rounded, 8, keep_count)


def freeze_past_policies(
    evidence: PastEvidence, suite, config: dict
) -> dict[str, object]:
    """Build immutable selections using PastEvidence only."""
    tables = evidence.table_by_bank()
    if set(tables) != {bank.bank_id for bank in suite.dataset.banks}:
        raise ValueError("past evidence bank set mismatch")
    past_view = suite.past_view()
    bank_results = []
    for bank in suite.dataset.banks:
        table = tables[bank.bank_id]
        game = analyze_game(
            table,
            keep_counts=config["keep_counts"],
            random_seeds=config["random_seeds"],
            bank=bank,
        )
        fit3 = _coefficient_map(game["surrogate_fits"]["3"]["coefficients"])
        selections = [dict(row) for row in game["retention_in_sample"]]
        for keep_count in config["keep_counts"]:
            extra_masks = {
                "cubic": _canonical_interaction_mask(fit3, keep_count),
                "recency_position": item_value_mask(
                    {i: float(i) for i in range(8)}, 8, keep_count
                ),
                "query_overlap": item_value_mask(
                    _query_overlap_weights(bank, past_view.for_bank(bank.bank_id)),
                    8,
                    keep_count,
                ),
                "lexical_centrality": item_value_mask(
                    _lexical_centrality_weights(bank), 8, keep_count
                ),
            }
            for policy, mask in extra_masks.items():
                index = mask_to_index(mask)
                selections.append(
                    {
                        "policy": policy,
                        "mask_index": index,
                        "keep_count": keep_count,
                        "actual_deletion_ratio": 1 - keep_count / 8,
                        "accuracy_in_sample": table[index],
                        **retained_payload_cost(bank, mask),
                    }
                )
        keys = [(row["policy"], row["keep_count"]) for row in selections]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate frozen policy/budget selection")
        for keep_count in config["keep_counts"]:
            masks = [
                index_to_mask(row["mask_index"], 8)
                for row in selections
                if row["keep_count"] == keep_count
            ]
            validate_equal_cardinality_costs(bank, masks, keep_count)
        bank_results.append(
            {
                "bank_id": bank.bank_id,
                "past_table_sha256": _json_hash(table),
                "past_game": game,
                "selections": sorted(
                    selections, key=lambda row: (row["policy"], row["keep_count"])
                ),
                "cost_audit": equal_length_bank_audit(bank),
            }
        )
    return {
        "schema_version": 1,
        "protocol": config["protocol"],
        "scope": "past-only policy freeze; no future outcomes",
        "past_evidence_sha256": evidence.sha256,
        "config_sha256": _json_hash(config),
        "public_manifest_sha256": _json_hash(suite.public_manifest()),
        "primary_policy": "quadratic",
        "primary_item_baseline": "exact_shapley",
        "severe_keep_counts": [2, 3],
        "bank_results": bank_results,
        "support_metadata_used": False,
        "future_data_used": False,
        "historical_test_access": False,
    }


def future_mask_indices(
    frozen: dict, probe_indices: tuple[int, ...]
) -> dict[str, tuple[int, ...]]:
    if not probe_indices or any(type(index) is not int or not 0 <= index < 256 for index in probe_indices):
        raise ValueError("invalid future prediction probe")
    result = {}
    for bank in frozen["bank_results"]:
        indices = {0, 255, *probe_indices}
        indices.update(row["mask_index"] for row in bank["selections"])
        result[bank["bank_id"]] = tuple(sorted(indices))
    return result


def _sign_flip_test(values: list[float], seed: int, resamples: int) -> dict[str, object]:
    if len(values) < 2:
        raise ValueError("paired randomization requires at least two banks")
    observed = fmean(values)
    if len(values) <= 18:
        null = [
            fmean(value * (1 if bits & (1 << i) else -1) for i, value in enumerate(values))
            for bits in range(1 << len(values))
        ]
        mode = "exact"
    else:
        rng = random.Random(seed)
        null = [
            fmean(value * rng.choice((-1, 1)) for value in values)
            for _ in range(resamples)
        ]
        mode = "monte_carlo"
    extreme = sum(value >= observed for value in null)
    p_value = (
        extreme / len(null)
        if mode == "exact"
        else (1 + extreme) / (len(null) + 1)
    )
    return {
        "mode": mode,
        "alternative": "interaction_greater_than_item",
        "p_value": p_value,
        "observed_mean": observed,
        "null_draws": len(null),
        "seed": seed if mode == "monte_carlo" else None,
    }


def summarize_future(
    rows: list[dict], suite, config: dict, frozen: dict, probe_indices: tuple[int, ...]
) -> dict[str, object]:
    if any(row.get("split") != "future" for row in rows):
        raise PermissionError("future analysis accepts future rows only")
    masks_by_bank = future_mask_indices(frozen, probe_indices)
    expected = {
        case["case_id"] for case in suite.future_conditions(masks_by_bank)
    }
    if len(rows) != len(expected) or {row["case_id"] for row in rows} != expected:
        raise ValueError("future analysis requires exactly the frozen/probe conditions")
    by_bank_mask: dict[tuple[str, int], list[dict]] = {}
    for row in rows:
        by_bank_mask.setdefault((row["bank_id"], row["mask_index"]), []).append(row)
    future_queries_per_bank = len(suite.future_view().for_bank(suite.dataset.banks[0].bank_id))
    if any(len(group) != future_queries_per_bank for group in by_bank_mask.values()):
        raise ValueError("future mask outcomes have inconsistent query counts")

    bank_lookup = {bank["bank_id"]: bank for bank in frozen["bank_results"]}
    bank_results = []
    primary_differences = []
    for bank in suite.dataset.banks:
        frozen_bank = bank_lookup[bank.bank_id]
        full = outcome_breakdown(by_bank_mask[(bank.bank_id, 255)])
        empty = outcome_breakdown(by_bank_mask[(bank.bank_id, 0)])
        retention = []
        for selection in frozen_bank["selections"]:
            outcome = outcome_breakdown(
                by_bank_mask[(bank.bank_id, selection["mask_index"])]
            )
            normalized = normalized_memory_retention(
                outcome["accuracy"], empty["accuracy"], full["accuracy"]
            )
            family_outcomes = {}
            for family in ("direct", "and2", "or2", "and3"):
                family_rows = [
                    row
                    for row in by_bank_mask[(bank.bank_id, selection["mask_index"])]
                    if row["family"] == family
                ]
                family_outcomes[family] = outcome_breakdown(family_rows)
            retention.append(
                {
                    "policy": selection["policy"],
                    "keep_count": selection["keep_count"],
                    "mask_index": selection["mask_index"],
                    "actual_deletion_ratio": selection["actual_deletion_ratio"],
                    "payload_bytes": selection["payload_bytes"],
                    "payload_whitespace_tokens": selection["payload_whitespace_tokens"],
                    "outcomes": outcome,
                    "normalized_memory_retention": normalized,
                    "family_outcomes": family_outcomes,
                }
            )
        retention_lookup = {
            (row["policy"], row["keep_count"]): row for row in retention
        }
        deltas = []
        for keep in (2, 3):
            interaction = retention_lookup[("quadratic", keep)]["outcomes"]["accuracy"]
            item = retention_lookup[("exact_shapley", keep)]["outcomes"]["accuracy"]
            deltas.append(interaction - item)
        primary = fmean(deltas)
        primary_differences.append(primary)

        actual_probe = [
            fmean(row["reward"] for row in by_bank_mask[(bank.bank_id, index)])
            for index in probe_indices
        ]
        prediction = {}
        for order in ("1", "2", "3"):
            coefficients = _coefficient_map(
                frozen_bank["past_game"]["surrogate_fits"][order]["coefficients"]
            )
            predicted = _predict(coefficients, list(probe_indices))
            metrics = prediction_metrics(actual_probe, predicted)
            k = min(10, len(probe_indices))
            predicted_top = set(
                sorted(range(len(predicted)), key=lambda i: (-predicted[i], probe_indices[i]))[:k]
            )
            actual_top = set(
                sorted(range(len(actual_probe)), key=lambda i: (-actual_probe[i], probe_indices[i]))[:k]
            )
            correlation = spearmanr(predicted, actual_probe).statistic
            prediction[order] = {
                **metrics,
                "spearman": float(correlation) if math.isfinite(float(correlation)) else None,
                "top_10_overlap": len(predicted_top & actual_top) / k,
                "n_probe_masks": len(probe_indices),
            }
        bank_results.append(
            {
                "bank_id": bank.bank_id,
                "full_outcomes": full,
                "empty_outcomes": empty,
                "retention": retention,
                "primary_severe_accuracy_difference": primary,
                "per_keep_primary_difference": {"2": deltas[0], "3": deltas[1]},
                "future_prediction_from_past_fit": prediction,
            }
        )

    interval = paired_bank_interval(
        primary_differences,
        seed=config["analysis"]["bootstrap_seed"],
        resamples=config["analysis"]["bootstrap_resamples"],
    )
    permutation = _sign_flip_test(
        primary_differences,
        config["analysis"]["randomization_seed"],
        config["analysis"]["randomization_resamples"],
    )
    return {
        "scope": "prospective development cohort; no qualification or confirmation",
        "primary_estimand": (
            "bank mean of future original-accuracy quadratic minus exact-Shapley at keep 2/3"
        ),
        "primary_policy": "quadratic",
        "primary_item_baseline": "exact_shapley",
        "bank_results": bank_results,
        "primary_bank_differences": primary_differences,
        "primary_interval": interval,
        "primary_randomization": permutation,
        "practical_margin_declared": config["analysis"]["practical_margin"],
        "development_mean_exceeds_margin": (
            fmean(primary_differences) >= config["analysis"]["practical_margin"]
        ),
        "decision": None,
        "decision_note": "development evidence cannot advance E5 or unlock historical P2",
        "independent_base_banks": len(primary_differences),
        "query_rows_treated_as_independent": False,
        "support_used_for_selection": False,
        "future_refit_used_for_selection": False,
        "historical_test_access": False,
        "qualified": None,
        "test_access": False,
    }


__all__ = [
    "PastEvidence",
    "freeze_past_policies",
    "future_mask_indices",
    "summarize_future",
]
