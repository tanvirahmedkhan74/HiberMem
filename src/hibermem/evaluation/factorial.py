"""E3a descriptive diagnostics; original correctness remains the selection score."""

from __future__ import annotations

import random
from collections import defaultdict
from itertools import combinations
from math import factorial
from statistics import fmean

import numpy as np

from hibermem.coalition.masks import iter_masks
from hibermem.interactions.mobius import mobius_transform
from .mechanism import _budget_values, analyze_game
from .predictive import prediction_metrics


def outcome_breakdown(rows):
    """Unconditional contributions sum to accuracy; conditional rates have explicit n."""
    if not rows:
        raise ValueError("outcome breakdown requires records")
    supported = [r for r in rows if r["supported"]]
    unsupported = [r for r in rows if not r["supported"]]
    return {
        "n_conditions": len(rows), "accuracy": fmean(r["reward"] for r in rows),
        "supported_correct": fmean(r["reward"] * r["supported"] for r in rows),
        "unsupported_correct": fmean(r["reward"] * (not r["supported"]) for r in rows),
        "n_supported": len(supported), "n_unsupported": len(unsupported),
        "supported_accuracy": fmean(r["reward"] for r in supported) if supported else None,
        "unsupported_accuracy": fmean(r["reward"] for r in unsupported) if unsupported else None,
        "unsupported_abstention": fmean(r["abstained"] for r in unsupported) if unsupported else None,
        "unsupported_assertion": fmean(r["unsupported_assertion"] for r in unsupported) if unsupported else None,
        "parse_null_rate": fmean(r["parse_null"] for r in rows),
    }


def exact_pair_details(table):
    """Cross-check Mobius SII against factorial-weighted contextual differences."""
    coefficients = mobius_transform(table)
    n = len(coefficients).bit_length() - 1
    pairs = []
    for i, j in combinations(range(n), 2):
        bits = (1 << i) | (1 << j)
        contexts = [s for s in range(1 << n) if not s & bits]
        contrasts = [table[s | bits] - table[s | (1 << i)] - table[s | (1 << j)] + table[s]
                     for s in contexts]
        sii = sum(a / (s.bit_count() - 1) for s, a in enumerate(coefficients) if s & bits == bits)
        direct = sum(factorial(s.bit_count()) * factorial(n - s.bit_count() - 2) / factorial(n - 1) * d
                     for s, d in zip(contexts, contrasts, strict=True))
        if not np.isclose(sii, direct, rtol=1e-10, atol=1e-12):
            raise ValueError("independent exact SII definitions disagree")
        pairs.append({"players": [i, j], "sii": float(sii), "context_weighted_sii": float(direct),
                      "mobius_pair": float(coefficients[bits]), "local_contrast": float(contrasts[0]),
                      "full_context_contrast": float(contrasts[-1]),
                      "positive_contexts": sum(d > 1e-12 for d in contrasts),
                      "negative_contexts": sum(d < -1e-12 for d in contrasts),
                      "n_contexts": len(contexts)})
    return {"pairs": pairs,
            "mobius_l1_by_order": {str(k): float(sum(abs(a) for s, a in enumerate(coefficients)
                                                     if s.bit_count() == k)) for k in range(n + 1)},
            "submodularity_violating_contexts": sum(p["positive_contexts"] for p in pairs),
            "negative_single_item_marginals": sum(
                table[s | (1 << i)] < table[s] - 1e-12 for i in range(n)
                for s in range(1 << n) if not s & (1 << i)),
            "numerical_tolerance": 1e-12}


def _predict(coefficients, masks):
    return [sum(row["value"] for row in coefficients if all(mask[i] for i in row["players"]))
            for mask in masks]


def selection_score_tables(game):
    """Only observed correctness / fits; never accepts support or oracle labels."""
    table, n = game["coalition_values_mask_index_order"], game["n_memories"]
    masks = list(iter_masks(n))
    item_maps = {
        "exact_shapley": {int(i): v for i, v in game["exact_shapley_items"].items()},
        "surrogate_shapley": {int(i): v for i, v in game["surrogate_fits"]["2"]["surrogate_shapley_items"].items()},
        "additive": {r["players"][0]: r["value"] for r in game["surrogate_fits"]["1"]["coefficients"]
                     if len(r["players"]) == 1},
        "leave_one_out": {i: table[-1] - table[(1 << n) - 1 - (1 << i)] for i in range(n)},
    }
    scores = {name: [sum(round(weights[i], 12) for i, present in enumerate(mask) if present)
                     for mask in masks] for name, weights in item_maps.items()}
    scores.update({name: _predict(game["surrogate_fits"][order]["coefficients"], masks)
                   for name, order in (("quadratic", "2"), ("cubic", "3"))})
    return scores


def _canonical_best(indices, scores, n=8):
    return max(indices, key=lambda index: (round(scores[index], 12),
                                          tuple(-i for i in range(n) if index & (1 << i))))


def add_selection_diagnostics(game, table_rows, bank, config):
    scores = selection_score_tables(game)
    n = game["n_memories"]
    tie_rows = []
    for keep in config["keep_counts"]:
        indices = [i for i in range(1 << n) if i.bit_count() == keep]
        cubic = _canonical_best(indices, scores["cubic"], n)
        retained = [m for i, m in enumerate(bank.memories) if cubic & (1 << i)]
        game["retention_in_sample"].append({
            "policy": "cubic", "mask_index": cubic, "keep_count": keep,
            "actual_deletion_ratio": 1 - keep / n,
            "accuracy_in_sample": game["coalition_values_mask_index_order"][cubic],
            "payload_bytes": sum(m.storage_bytes for m in retained),
            "payload_whitespace_tokens": sum(m.storage_tokens for m in retained)})
        budget = _budget_values(game["coalition_values_mask_index_order"], n, keep)
        keep_scores = {**scores, "budget_marginal": [sum(round(budget[i], 12) for i in range(n)
                                                         if index & (1 << i)) for index in range(1 << n)]}
        for policy, values in keep_scores.items():
            best = max(round(values[i], 12) for i in indices)
            ties = [i for i in indices if round(values[i], 12) == best]
            for seed in config["random_seeds"]:
                index = random.Random(seed).choice(ties)
                tie_rows.append({"policy": policy, "keep_count": keep, "seed": seed,
                                 "n_tied_masks": len(ties), "mask_index": index,
                                 "outcomes": outcome_breakdown(table_rows[index])})
    for selection in game["retention_in_sample"]:
        selection["outcomes"] = outcome_breakdown(table_rows[selection["mask_index"]])
    game["randomized_tie_sensitivity"] = tie_rows
    game["tie_breaking"] = ("primary canonical choices plus uniform draws among maximal-score subsets; "
                            "12-decimal scores; seeds are not independent banks")


def summarize_factorial(rows, suite, config):
    by_query = defaultdict(dict)
    for row in rows:
        if row["mask_index"] in by_query[row["query_id"]]:
            raise ValueError("duplicate query coalition")
        by_query[row["query_id"]][row["mask_index"]] = row
    if set(by_query) != {q.query_id for q in suite.dataset.queries} or any(
            set(table) != set(range(256)) for table in by_query.values()):
        raise ValueError("all and only complete factorial coalition tables are required")
    queries = []
    for query in suite.dataset.queries:
        rr = [by_query[query.query_id][i] for i in range(256)]
        observed = exact_pair_details([r["reward"] for r in rr])
        oracle = exact_pair_details([float(r["supported"]) for r in rr])
        active = {i for support in suite.minimal_supports[query.query_id] for i in support}
        null_marginals = [abs(rr[s | (1 << i)]["reward"] - rr[s]["reward"])
                          for i in set(range(8)) - active for s in range(256) if not s & (1 << i)]
        queries.append({"query_id": query.query_id, **suite.query_metadata[query.query_id],
                        "outcomes": outcome_breakdown(rr), "observed_exact": observed,
                        "symbolic_reference": oracle,
                        "pair_sii_mae_from_symbolic_reference": fmean(abs(a["sii"] - b["sii"])
                            for a, b in zip(observed["pairs"], oracle["pairs"], strict=True)),
                        "max_abs_symbolically_null_player_marginal": max(null_marginals, default=0),
                        "interpretation": "oracle departure is behavioral, not exact-estimator error"})
    games, table_rows_by_bank = [], {}
    for bank in suite.dataset.banks:
        bank_queries = [q for q in suite.dataset.queries if q.bank_id == bank.bank_id]
        table_rows = {i: [by_query[q.query_id][i] for q in bank_queries] for i in range(256)}
        table_rows_by_bank[bank.bank_id] = table_rows
        table = [fmean(r["reward"] for r in table_rows[i]) for i in range(256)]
        game = {"bank_id": bank.bank_id, **suite.game_metadata[bank.bank_id],
                "outcomes": outcome_breakdown([r for rr in table_rows.values() for r in rr]),
                **analyze_game(table, keep_counts=config["keep_counts"], random_seeds=config["random_seeds"], bank=bank)}
        add_selection_diagnostics(game, table_rows, bank, config)
        games.append(game)

    # Freeze source choices and fits BEFORE referring to target outcomes. Same
    # facts/queries under a presentation intervention, explicitly not future data.
    game_lookup = {(g["base_bank_id"], g["family"], g["overlap"], g["world"], g["variant"]): g for g in games}
    presentation = []
    masks = list(iter_masks(8))
    for target in games:
        if target["variant"] == "original":
            continue
        key = (target["base_bank_id"], target["family"], target["overlap"], target["world"])
        source = game_lookup[(*key, "original")]
        delta = np.asarray(target["coalition_values_mask_index_order"]) - source["coalition_values_mask_index_order"]
        frozen = [{"policy": s["policy"], "keep_count": s["keep_count"], "mask_index": s["mask_index"],
                   "source_outcomes": s["outcomes"],
                   "target_outcomes": outcome_breakdown(table_rows_by_bank[target["bank_id"]][s["mask_index"]])}
                  for s in source["retention_in_sample"]]
        presentation.append({"source_bank_id": source["bank_id"], "target_bank_id": target["bank_id"],
                             "coalitions_changed": int(np.count_nonzero(delta)),
                             "mean_utility_change": float(delta.mean()), "frozen_selection_transfer": frozen,
                             "frozen_prediction_transfer": {
                                 order: prediction_metrics(target["coalition_values_mask_index_order"],
                                                           _predict(fit["coefficients"], masks))
                                 for order, fit in source["surrogate_fits"].items()},
                             "scope": "presentation transfer only; not future-query generalization"})
    overlap = []
    for high in games:
        if high["overlap"] != "high":
            continue
        low = game_lookup[(high["base_bank_id"], high["family"], "low", high["world"], high["variant"])]
        overlap.append({"low_bank_id": low["bank_id"], "high_bank_id": high["bank_id"],
                        "mean_record_token_jaccard_change": high["mean_record_token_jaccard"] - low["mean_record_token_jaccard"],
                        "mean_accuracy_change": high["outcomes"]["accuracy"] - low["outcomes"]["accuracy"],
                        "scope": "paired lexical-nuisance intervention, not semantic validation"})
    counterfactual = []
    query_lookup = {(m["base_bank_id"], m["family"], m["overlap"], m["world"], m["variant"], m["chain"]): q
                    for q, m in suite.query_metadata.items()}
    for query_id, meta in suite.query_metadata.items():
        if meta["world"] != "base":
            continue
        other_id = query_lookup[(meta["base_bank_id"], meta["family"], meta["overlap"], "counterfactual", meta["variant"], meta["chain"])]
        pairs = [(by_query[query_id][i], by_query[other_id][i]) for i in range(256)]
        same = [(a, b) for a, b in pairs if a["request_sha256"] == b["request_sha256"]]
        supported = [(a, b) for a, b in pairs if a["supported"] and b["supported"]]
        counterfactual.append({"base_query_id": query_id, "counterfactual_query_id": other_id,
                               "n_paired_conditions": len(pairs), "n_identical_prompts": len(same),
                               "identical_prompt_output_agreement": fmean(a["raw_output"] == b["raw_output"] for a, b in same) if same else None,
                               "n_supported_pairs": len(supported),
                               "supported_both_worlds_correct": fmean(a["reward"] * b["reward"] for a, b in supported),
                               "supported_output_change_rate": fmean(a["raw_output"] != b["raw_output"] for a, b in supported)})
    return {"games": games, "per_query": queries, "paired_counterfactuals": counterfactual,
            "paired_lexical_overlap": overlap, "paired_presentation": presentation,
            "future_queries_evaluated": 0, "primary_score": "full-world destination correctness",
            "support_score_scope": "secondary diagnostic; never used to fit or select operational masks",
            "independent_base_banks": suite.manifest()["independent_base_banks"],
            "uncertainty": "development descriptions only; no significance or population generalization claim"}
