"""Exact small-game diagnostics. No prospective or qualification claims."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from statistics import fmean

import numpy as np

from hibermem.coalition.masks import iter_masks, mask_to_index
from hibermem.interactions.mobius import mobius_transform, inverse_mobius_transform
from hibermem.interactions.polynomial import PolynomialInteractionEstimator
from hibermem.retention.policies import item_value_mask, mobius_to_shapley_items, random_mask
from .predictive import prediction_metrics, paired_bank_interval


def coefficient_rows(coefficients):
    return [{"players": list(term), "value": float(value)} for term, value in coefficients.items()]


def _budget_values(table, n, keep):
    # Expected marginal contribution to a uniformly chosen (keep-1)-item context.
    return {i: fmean(table[sum(1 << j for j in context) | (1 << i)]
                     - table[sum(1 << j for j in context)]
                     for context in combinations([j for j in range(n) if j != i], keep - 1))
            for i in range(n)}


def analyze_game(table, *, keep_counts, random_seeds, bank) -> dict:
    n = len(bank.memories)
    values = np.asarray(table, dtype=float)
    if values.shape != (1 << n,) or not np.isfinite(values).all():
        raise ValueError("a finite complete game table in mask-index order is required")
    masks = tuple(iter_masks(n))
    mobius = mobius_transform(values)
    terms = {tuple(i for i in range(n) if index & (1 << i)): value
             for index, value in enumerate(mobius)}
    exact_items = mobius_to_shapley_items(terms, n)
    sii = {pair: sum(value / (len(term) - 1) for term, value in terms.items()
                     if set(pair) <= set(term)) for pair in combinations(range(n), 2)}
    fits = {order: PolynomialInteractionEstimator(max_order=order, n_players=n).fit(masks, values)
            for order in (1, 2, 3)}
    fit_rows = {}
    for order, fit in fits.items():
        fit_rows[str(order)] = {
            "coefficient_semantics": "Mobius coefficients of fitted surrogate, not exact observed-game SII",
            "coefficients": coefficient_rows(fit.coefficients),
            "surrogate_shapley_items": {str(k): v for k, v in fit.shapley_item_values().items()},
            "prediction_metrics_in_sample": prediction_metrics(values, fit.predict(masks)),
            "empty_prediction_error": fit.predict([masks[0]])[0] - float(values[0]),
            "full_prediction_error": fit.predict([masks[-1]])[0] - float(values[-1]),
            "condition_number": fit.condition_number,
        }
    selections = []
    pair_terms = sorted(fits[2].interactions(2))
    for keep in keep_counts:
        candidates = [mask for mask in masks if sum(mask) == keep]

        def choose_polynomial(coefficients):
            # Complete-table fits should not select different tied subsets merely
            # because Windows/Linux LAPACK differ in their final rounding bits.
            return max(candidates, key=lambda mask: (
                round(sum(value for term, value in coefficients.items() if all(mask[i] for i in term)), 12),
                tuple(-i for i, present in enumerate(mask) if present)))

        item_methods = {
            "exact_shapley": exact_items,
            "surrogate_shapley": fits[2].shapley_item_values(),
            "additive": fits[1].singleton_coefficients(),
            "leave_one_out": {i: float(values[-1] - values[(1 << n) - 1 - (1 << i)]) for i in range(n)},
            "budget_marginal": _budget_values(values, n, keep),
        }
        chosen = {name: item_value_mask({i: round(w, 12) for i, w in weights.items()}, n, keep)
                  for name, weights in item_methods.items()}
        chosen["quadratic"] = choose_polynomial(fits[2].coefficients)
        chosen["oracle_in_sample_ceiling"] = max(candidates, key=lambda mask: (values[mask_to_index(mask)],
                                                                             tuple(-i for i, x in enumerate(mask) if x)))
        for seed in random_seeds:
            chosen[f"random_seed_{seed}"] = random_mask(n, keep, seed)
            shuffled = dict(fits[2].coefficients)
            weights = np.random.default_rng(seed).permutation([shuffled[pair] for pair in pair_terms])
            shuffled.update(zip(pair_terms, map(float, weights), strict=True))
            chosen[f"shuffled_pairs_seed_{seed}"] = choose_polynomial(shuffled)
        for name, mask in chosen.items():
            retained = [m for m, present in zip(bank.memories, mask, strict=True) if present]
            selections.append({
                "policy": name, "mask_index": mask_to_index(mask), "keep_count": keep,
                "actual_deletion_ratio": 1 - keep / n,
                "accuracy_in_sample": float(values[mask_to_index(mask)]),
                "payload_bytes": sum(m.storage_bytes for m in retained),
                "payload_whitespace_tokens": sum(m.storage_tokens for m in retained),
            })
    return {
        "scope": "same-query descriptive diagnostics; not future-policy validation",
        "n_memories": n, "coalition_values_mask_index_order": list(map(float, values)),
        "empty_accuracy": float(values[0]), "full_accuracy": float(values[-1]),
        "exact_mobius": coefficient_rows(terms), "exact_sii_pairs": coefficient_rows(sii),
        "exact_shapley_items": {str(k): v for k, v in exact_items.items()},
        "shapley_efficiency_error": float(sum(exact_items.values()) - (values[-1] - values[0])),
        "reconstruction_max_error": float(np.max(np.abs(np.asarray(inverse_mobius_transform(mobius)) - values))),
        "surrogate_fits": fit_rows, "retention_in_sample": selections,
        "tie_breaking": "12-decimal selection scores then canonical player order; randomized tie sensitivity not tested",
        "cost_scope": "payload only; no total-system or tokenizer-budget claim",
    }


def summarize_mechanism(rows, suite, config):
    by_query = defaultdict(dict)
    for row in rows:
        if row["mask_index"] in by_query[row["query_id"]]:
            raise ValueError("duplicate coalition for query")
        by_query[row["query_id"]][row["mask_index"]] = row
    expected = {query.query_id for query in suite.dataset.queries}
    if set(by_query) != expected or any(set(table) != set(range(256)) for table in by_query.values()):
        raise ValueError("all and only complete query coalition tables are required")
    per_query, games = [], []
    for query in suite.dataset.queries:
        table = [by_query[query.query_id][i]["reward"] for i in range(256)]
        i, j = suite.required_pairs[query.query_id]
        pair = (1 << i) | (1 << j)
        context = 255 ^ pair
        per_query.append({
            "query_id": query.query_id, "bank_id": query.bank_id,
            **suite.game_metadata[query.bank_id], "dependency_group": query.dependency_group,
            "required_pair_diagnostic_only": [i, j],
            "local_pair_interaction": table[pair] - table[1 << i] - table[1 << j] + table[0],
            "full_context_pair_interaction": table[255] - table[context | (1 << i)] - table[context | (1 << j)] + table[context],
            "pair_only_accuracy": table[pair],
            "first_only_accuracy": table[1 << i], "second_only_accuracy": table[1 << j],
        })
    for bank in suite.dataset.banks:
        queries = [q for q in suite.dataset.queries if q.bank_id == bank.bank_id]
        table = [fmean(by_query[q.query_id][i]["reward"] for q in queries) for i in range(256)]
        bank_rows = [row for query in queries for row in by_query[query.query_id].values()]
        unsupported = [row for row in bank_rows if not row["supported"]]
        games.append({"bank_id": bank.bank_id, **suite.game_metadata[bank.bank_id],
                      "n_queries": len(queries),
                      "unsupported_abstention": fmean(row["abstained"] for row in unsupported),
                      "unsupported_correctness": fmean(row["reward"] for row in unsupported),
                      "parse_null_rate": fmean(row["parse_null"] for row in bank_rows),
                      **analyze_game(table, keep_counts=config["keep_counts"],
                                     random_seeds=config["random_seeds"], bank=bank)})
    paired = []
    for game in games:
        if game["variant"] == "original":
            continue
        original = next(g for g in games if g["base_bank_id"] == game["base_bank_id"] and g["variant"] == "original")
        delta = np.array(game["coalition_values_mask_index_order"]) - original["coalition_values_mask_index_order"]
        paired.append({"base_bank_id": game["base_bank_id"], "variant": game["variant"],
                       "mean_utility_change": float(delta.mean()),
                       "max_absolute_utility_change": float(abs(delta).max()),
                       "coalitions_with_changed_mean_reward": int(np.count_nonzero(delta))})
    return {"games": games, "query_pair_contrasts": per_query,
            "paired_presentation_sensitivity": paired,
            "uncertainty": "no confidence/generalization claim from this small development pilot",
            "future_queries_evaluated": 0}


def local_v2_contrasts(rows):
    """For use ONLY after the caller validates the original v2 artifact bundle."""
    needed = {"pair_only", "missing_first_minimal", "missing_second_minimal", "empty"}
    grouped = defaultdict(dict)
    for row in rows:
        if row["kind"] == "two_hop" and row["condition"] in needed:
            if row["condition"] in grouped[row["query_id"]]:
                raise ValueError("duplicate local contrast condition")
            grouped[row["query_id"]][row["condition"]] = row
    banks = defaultdict(list)
    for conditions in grouped.values():
        if set(conditions) != needed:
            raise ValueError("incomplete four-corner contrast")
        reward = {key: value["reward"] for key, value in conditions.items()}
        banks[conditions["pair_only"]["base_bank_id"]].append(
            reward["pair_only"] - reward["missing_first_minimal"]
            - reward["missing_second_minimal"] + reward["empty"])
    means = {key: fmean(value) for key, value in sorted(banks.items())}
    if not means:
        raise ValueError("no complete local contrasts")
    return {"scope": "exploratory local empty-context pair contrast, not SII or future retention",
            "query_count": len(grouped), "bank_means": means,
            "bank_bootstrap": paired_bank_interval(list(means.values())) if len(means) > 1 else None,
            "mean": fmean(means.values()), "scientific_gate_eligible": False,
            "confirmation_compatible": False, "selected_candidate": None}
