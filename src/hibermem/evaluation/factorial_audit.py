"""Read-only E3 artifact audits; no changes to scoring, reports, or qualification."""

from __future__ import annotations

import copy
import json
from collections import defaultdict
from pathlib import Path
from statistics import fmean

from hibermem.environments.controlled.factorial import PROTOCOL
from .factorial import outcome_breakdown


def reference_pair_summary(pairs, *, numerical_tolerance=1e-12):
    return {"n": len(pairs), "mean": fmean(o["sii"] for o, _ in pairs) if pairs else None,
            "sign_matches_reference": sum(abs(o["sii"]) > numerical_tolerance and o["sii"] * t["sii"] > 0
                                          for o, t in pairs),
            "numerically_zero": sum(abs(o["sii"]) <= numerical_tolerance for o, _ in pairs),
            "numerical_tolerance": numerical_tolerance,
            "interpretation": "roundoff exclusion only, not a practical-effect or significance threshold"}


def decoding_counts(rows, budget):
    capped = [r for r in rows if r["output_tokens"] >= budget]
    return {"n": len(rows), "at_generation_limit": len(capped),
            "at_limit_rate": len(capped) / len(rows) if rows else None,
            "parse_null": sum(r["parse_null"] for r in rows),
            "parse_null_at_limit": sum(r["parse_null"] for r in capped),
            "strict_format": sum(r["strict_format"] for r in rows),
            "interpretation": "length-cap hits are observed; recovery with more tokens is not assumed"}


def summarize_bundle(report, rows, config):
    """Pure aggregation; public file entry point validates all evidence first."""
    analysis = report["analysis"]
    game_meta = {g["bank_id"]: g for g in analysis["games"]}
    query_meta = {q["query_id"]: q for q in analysis["per_query"]}
    families = {}
    budget = config["generation"]["max_new_tokens"]
    for family in config["families"]:
        rr = [r for r in rows if game_meta[r["bank_id"]]["family"] == family]
        games = [g for g in analysis["games"] if g["family"] == family]
        queries = [q for q in analysis["per_query"] if q["family"] == family]
        full = [r for r in rr if r["mask_index"] == 255]
        target_pairs = [(o, t) for q in queries for o, t in zip(
            q["observed_exact"]["pairs"], q["symbolic_reference"]["pairs"], strict=True) if abs(t["sii"]) > 1e-12]
        selections = defaultdict(list)
        severe, by_bank = defaultdict(list), defaultdict(lambda: defaultdict(list))
        for game in games:
            for s in game["retention_in_sample"]:
                selections[(s["policy"], s["keep_count"])].append(s["outcomes"])
                if s["actual_deletion_ratio"] > .5:
                    severe[s["policy"]].append(s["outcomes"])
                    by_bank[game["base_bank_id"]][s["policy"]].append(s["outcomes"])

        def average(outcomes):
            return {k: fmean(o[k] for o in outcomes)
                    for k in ("accuracy", "supported_correct", "unsupported_correct")}

        cf = [c for c in analysis["paired_counterfactuals"] if query_meta[c["base_query_id"]]["family"] == family]
        lexical = [c for c in analysis["paired_lexical_overlap"] if game_meta[c["high_bank_id"]]["family"] == family]
        families[family] = {
            "n_games": len(games), "n_query_records": len(queries),
            "outcomes": outcome_breakdown(rr), "full_outcomes": outcome_breakdown(full),
            "decoding_all": decoding_counts(rr, budget),
            "decoding_supported": decoding_counts([r for r in rr if r["supported"]], budget),
            "full_errors_at_limit": sum(not r["reward"] and r["output_tokens"] >= budget for r in full),
            "target_pair_sii": reference_pair_summary(target_pairs),
            "mean_pair_sii_mae_from_symbolic": fmean(q["pair_sii_mae_from_symbolic_reference"] for q in queries),
            "mean_supported_both_worlds_correct": fmean(c["supported_both_worlds_correct"] for c in cf),
            "mean_lexical_accuracy_delta": fmean(c["mean_accuracy_change"] for c in lexical),
            "mean_in_sample_r2": {order: fmean(values) if values else None for order in ("1", "2", "3")
                                  for values in [[g["surrogate_fits"][order]["prediction_metrics_in_sample"]["r2"]
                                                  for g in games if g["surrogate_fits"][order]["prediction_metrics_in_sample"]["r2"] is not None]]},
            "n_defined_in_sample_r2": {order: sum(g["surrogate_fits"][order]["prediction_metrics_in_sample"]["r2"] is not None
                                                   for g in games) for order in ("1", "2", "3")},
            "retention_in_sample": [{"policy": policy, "keep_count": keep, **average(outcomes)}
                                     for (policy, keep), outcomes in sorted(selections.items())],
            "severe_retention_in_sample": {p: average(o) for p, o in sorted(severe.items())},
            "severe_by_base_bank": {b: {p: average(o) for p, o in sorted(policies.items())}
                                    for b, policies in sorted(by_bank.items())},
        }
    return {"audit_schema_version": 2, "protocol": PROTOCOL, "scope": "read-only descriptive reanalysis; no qualification",
            "identity": report["identity"], "engineering_only": report["engineering_only"],
            "independent_base_banks": analysis["independent_base_banks"], "families": families,
            "decoding_all": decoding_counts(rows, budget), "max_new_tokens": budget,
            "future_queries_evaluated": 0, "qualified": None, "test_access": False}


def compare_bundles(short, long):
    """Require identical design except a larger cap; audit, never assume, prefixes.

    Each bundle is (report, rows, config, runtime), already independently validated
    by the file entry point. Runtime/prefix mismatches are reported, not hidden.
    """
    sr, srows, sc, st = short
    lr, lrows, lc, lt = long
    sc0, lc0 = copy.deepcopy(sc), copy.deepcopy(lc)
    sb = sc0["generation"].pop("max_new_tokens")
    lb = lc0["generation"].pop("max_new_tokens")
    if sc0 != lc0 or lb <= sb:
        raise ValueError("comparison requires the same design and a strictly larger decoding cap")
    for key in ("candidate", "backend", "suite_sha256", "prompt_template_sha256"):
        if sr["identity"][key] != lr["identity"][key]:
            raise ValueError(f"comparison identity mismatch: {key}")
    if sr["engineering_only"] != lr["engineering_only"]:
        raise ValueError("cannot compare real and mock evidence")
    old = {r["case_id"]: r for r in srows}
    new = {r["case_id"]: r for r in lrows}
    if not old or len(old) != len(srows) or len(new) != len(lrows) or old.keys() != new.keys():
        raise ValueError("comparison requires exactly matched unique conditions")
    runtime_keys = (set(st) | set(lt)) - {"source_tree_sha256"}
    runtime_differences = sorted(k for k in runtime_keys if k not in st or k not in lt or st[k] != lt[k])
    prefix_mismatches, input_mismatches, early_stop_changes = [], [], []
    transitions = defaultdict(int)
    meta = {g["bank_id"]: g for g in sr["analysis"]["games"]}
    by_family = defaultdict(list)
    for case_id, a in old.items():
        b = new[case_id]
        if a["request_sha256"] != b["request_sha256"] or a["messages"] != b["messages"]:
            raise ValueError(f"paired prompt mismatch: {case_id}")
        if not sr["engineering_only"]:
            at, bt = a["generation_trace"], b["generation_trace"]
            if at["input_token_ids"] != bt["input_token_ids"] or at["rendered_prompt"] != bt["rendered_prompt"]:
                input_mismatches.append(case_id)
            if at["generated_token_ids"] != bt["generated_token_ids"][:len(at["generated_token_ids"])]:
                prefix_mismatches.append(case_id)
            if a["output_tokens"] < sb and (at["generated_token_ids"] != bt["generated_token_ids"] or a["raw_output"] != b["raw_output"]):
                early_stop_changes.append(case_id)
        transition = f"{int(a['reward'])}_to_{int(b['reward'])}"
        transitions[transition] += 1
        by_family[meta[a["bank_id"]]["family"]].append((a, b))
    eligible = (not sr["engineering_only"] and not runtime_differences and not prefix_mismatches
                and not input_mismatches and not early_stop_changes)
    return {"scope": "paired development decoding-budget diagnostic; not future-policy validation",
            "short_budget": sb, "long_budget": lb, "n_pairs": len(old),
            "short_identity": sr["identity"], "long_identity": lr["identity"],
            "runtime_differences": runtime_differences,
            "input_token_mismatches": input_mismatches, "prefix_mismatches": prefix_mismatches,
            "previously_early_stopped_changes": early_stop_changes,
            "matched_decode_only_evidence": eligible,
            "reward_transitions": dict(sorted(transitions.items())),
            "family_changes": {f: {"n_pairs": len(pairs),
                                   "accuracy_delta": fmean(b["reward"] - a["reward"] for a, b in pairs),
                                   "supported_correct_delta": fmean(b["reward"] * b["supported"] - a["reward"] * a["supported"] for a, b in pairs),
                                   "previously_capped": sum(a["output_tokens"] >= sb for a, b in pairs),
                                   "capped_wrong_to_correct": sum(a["output_tokens"] >= sb and not a["reward"] and b["reward"] == 1 for a, b in pairs)}
                               for f, pairs in sorted(by_family.items())},
            "qualified": None, "test_access": False,
            "interpretation": "prefix/runtime agreement supports a paired diagnostic, never model qualification"}


def read_validated_bundle(path: Path, *, allow_mock=False):
    from hibermem.experiments.exact_mechanism import validate_mechanism_report
    report = validate_mechanism_report(path, allow_mock=allow_mock)
    if report["protocol"] != PROTOCOL:
        raise ValueError("factorial audit requires an E3 report")
    def read(name):
        return json.loads(path.with_name(name).read_text(encoding="utf-8"))
    return report, read("evaluations.json"), read("config.json"), read("runtime.json")
