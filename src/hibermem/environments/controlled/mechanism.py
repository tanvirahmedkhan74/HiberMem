"""Fresh development-only complete coalition games, not a qualification suite."""

from __future__ import annotations

from dataclasses import dataclass, replace

from hibermem.coalition.masks import iter_masks, mask_to_index
from .calibration import generate_calibration_v2
from .dataset import ControlledDataset, MemoryBank, QuerySplit
from .prompts import build_messages

PROTOCOL = "phase2r-exact-mechanism-v1"
VARIANTS = ("original", "reverse_records", "reverse_options")


@dataclass(frozen=True)
class MechanismSuite:
    dataset: ControlledDataset
    required_pairs: dict[str, tuple[int, int]]
    game_metadata: dict[str, dict]

    def manifest(self) -> dict:
        return {
            **self.dataset.public_manifest(),
            "protocol": PROTOCOL,
            "scope": "development_only",
            "required_pairs_diagnostic_only": {key: list(value) for key, value in self.required_pairs.items()},
            "games": self.game_metadata,
            "planned_conditions": len(self.dataset.queries) * 256,
            "query_shift": "none; E2 variants change presentation only",
            "history": "fresh system and user messages for every condition",
        }

    def conditions(self):
        view = self.dataset.view(QuerySplit.DISCOVERY)
        for query in self.dataset.queries:
            bank = self.dataset.bank(query.bank_id)
            for mask in iter_masks(len(bank.memories)):
                memories = tuple(m for m, present in zip(bank.memories, mask, strict=True) if present)
                messages = build_messages(memories, query)
                if self.game_metadata[bank.bank_id]["variant"] == "reverse_records":
                    # Change presentation order only. Keep logical players and M_i
                    # labels fixed, so relabeling is not confounded with order.
                    record_section, separator, task_section = messages[1]["content"].partition("\n\nTask: ")
                    header, newline, records = record_section.partition("\n")
                    if not separator or not newline:
                        raise ValueError("unexpected base prompt layout")
                    messages[1] = {"role": "user", "content": header + newline
                                   + "\n".join(reversed(records.splitlines())) + separator + task_section}
                yield {
                    "case_id": f"{query.query_id}:{mask_to_index(mask):03d}",
                    "bank": bank, "query": query, "view": view, "mask": mask,
                    "messages": messages,
                    "supported": all(mask[i] for i in self.required_pairs[query.query_id]),
                }


def generate_mechanism_suite(*, n_banks: int, bank_start: int, seed: int,
                             variants: list[str]) -> MechanismSuite:
    # Reserve 320..339 for this version. Never instantiate confirmation/test banks.
    if any(type(value) is not int for value in (n_banks, bank_start, seed)):
        raise ValueError("integer development bank/seed settings required")
    if n_banks < 1 or bank_start < 320 or bank_start + n_banks > 340:
        raise ValueError("exact mechanism development banks must stay inside [320,340)")
    if not variants or variants[0] != "original" or len(set(variants)) != len(variants):
        raise ValueError("unique variants starting with original are required")
    if any(variant not in VARIANTS for variant in variants):
        raise ValueError("unsupported presentation variant")
    base = generate_calibration_v2(n_banks, bank_start=bank_start, seed=seed)
    selected = [case for case in base.cases if case.condition == "pair_only"
                and case.query.template_family == "dev-two_hop-0"]
    banks, queries, answers, pairs, metadata = {}, [], {}, {}, {}
    for case in selected:
        original_query = case.query
        original_bank = base.dataset.bank(original_query.bank_id)
        base_view = base.dataset.view(QuerySplit.DISCOVERY)
        answer = next(option for option in original_query.options
                      if base_view.score(original_query, option) == 1)
        for variant in variants:
            bank_id = f"{original_bank.bank_id}-{variant}"
            banks[bank_id] = MemoryBank(bank_id, tuple(
                replace(memory, bank_id=bank_id)
                for memory in original_bank.memories
            ))
            # Tuple order is the logical player order, independent of presentation.
            query = replace(original_query, bank_id=bank_id,
                            query_id=f"{original_query.query_id}-{variant}",
                            options=(original_query.options[::-1] if variant == "reverse_options"
                                     else original_query.options))
            queries.append(query)
            answers[query.query_id] = answer
            pairs[query.query_id] = tuple(i for i, present in enumerate(case.mask) if present)
            metadata[bank_id] = {"base_bank_id": case.base_bank_id, "variant": variant}
    dataset = ControlledDataset(banks=tuple(banks.values()), queries=tuple(queries),
                                answers=answers, version=PROTOCOL)
    if len(queries) != n_banks * len(variants) * 4 or any(
        query.split is not QuerySplit.DISCOVERY for query in queries
    ):
        raise ValueError("mechanism suite must contain exactly four discovery queries per game")
    return MechanismSuite(dataset, pairs, metadata)
