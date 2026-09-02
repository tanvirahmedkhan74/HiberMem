"""Leakage-scoped past/future memory games for E4.

The first E4 protocol tests a deliberately narrow paraphrase shift over a mixed
direct/AND2/OR2/AND3 bank. Past and future are distinct query capabilities. Support
antichains exist for controls/diagnostics but are never exposed through PastEvidence
or retention-policy interfaces.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from hibermem.coalition.masks import index_to_mask, iter_masks, mask_to_index
from hibermem.memory import MemoryItem

from .contract import build_contract_messages, contract_prompt_hash
from .dataset import ControlledDataset, EvaluationView, MemoryBank, Query, QuerySplit
from .factorial import FactorialOracle, supported_by


PROTOCOL = "phase2r-prospective-retention-v1"
FAMILIES = ("direct", "and2", "or2", "and3")
SHIFT = "paraphrase_v1"

PAST_TEMPLATES = (
    "Past dispatch alpha. Which destination is reachable from {request}?",
    "Past dispatch beta. Which destination is reachable from {request}?",
)
FUTURE_TEMPLATES = (
    "Future dispatch gamma. Which destination is reachable from {request}?",
    "Future dispatch delta. Which destination is reachable from {request}?",
    "Future dispatch epsilon. Which destination is reachable from {request}?",
)


class PastQueryCapability:
    """Only this capability may be converted into policy-fitting evidence."""

    def __init__(self, view: EvaluationView):
        if view.split is not QuerySplit.PAST:
            raise ValueError("past capability requires the past split")
        self._view = view
        self.split = QuerySplit.PAST
        self.queries = view.queries

    def for_bank(self, bank_id: str) -> tuple[Query, ...]:
        return self._view.for_bank(bank_id)

    def authorize(self, query: Query) -> None:
        self._view.authorize(query)

    def score(self, query: Query, parsed_action: str | None) -> float:
        return self._view.score(query, parsed_action)

    def scoring_fingerprint(self, query: Query) -> str:
        return self._view.scoring_fingerprint(query)


class FutureQueryCapability:
    """Scoring-only capability; fitting APIs must reject this type."""

    def __init__(self, view: EvaluationView):
        if view.split is not QuerySplit.FUTURE:
            raise ValueError("future capability requires the future split")
        self._view = view
        self.split = QuerySplit.FUTURE
        self.queries = view.queries

    def for_bank(self, bank_id: str) -> tuple[Query, ...]:
        return self._view.for_bank(bank_id)

    def authorize(self, query: Query) -> None:
        self._view.authorize(query)

    def score(self, query: Query, parsed_action: str | None) -> float:
        return self._view.score(query, parsed_action)

    def scoring_fingerprint(self, query: Query) -> str:
        return self._view.scoring_fingerprint(query)


@dataclass(frozen=True)
class ProspectiveSuite:
    dataset: ControlledDataset
    minimal_supports: Mapping[str, tuple[tuple[int, ...], ...]]
    query_metadata: Mapping[str, dict]
    bank_metadata: Mapping[str, dict]
    output_contract: str

    def past_view(self) -> PastQueryCapability:
        return PastQueryCapability(self.dataset.view(QuerySplit.PAST))

    def future_view(self) -> FutureQueryCapability:
        return FutureQueryCapability(self.dataset.view(QuerySplit.FUTURE))

    def public_manifest(self) -> dict[str, object]:
        past = self.past_view()
        future = self.future_view()
        banks = [
            {
                "bank_id": bank.bank_id,
                "memories": [
                    {
                        "memory_id": memory.memory_id,
                        "position": memory.position,
                        "text": memory.text,
                        "storage_bytes": memory.storage_bytes,
                        "storage_tokens": memory.storage_tokens,
                    }
                    for memory in bank.memories
                ],
                "metadata": self.bank_metadata[bank.bank_id],
            }
            for bank in self.dataset.banks
        ]
        past_queries = [_query_public(query) for query in past.queries]
        future_commitments = [
            {
                "query_id": query.query_id,
                "commitment_sha256": _query_commitment(query, future),
            }
            for query in future.queries
        ]
        return {
            "schema_version": 1,
            "protocol": PROTOCOL,
            "scope": "development_prospective",
            "output_contract": self.output_contract,
            "output_contract_prompt_sha256": contract_prompt_hash(self.output_contract),
            "banks": banks,
            "past_queries": past_queries,
            "future_query_commitments": future_commitments,
            "n_banks": len(banks),
            "n_memories": 8,
            "n_past_queries": len(past_queries),
            "n_future_queries": len(future_commitments),
            "past_planned_conditions": len(past_queries) * 256,
            "future_content_exposed": False,
            "support_metadata_exposed_to_policy": False,
            "query_shift": SHIFT,
            "independent_unit": "base memory bank",
            "historical_phase2_test_access": False,
        }

    def sealed_future_manifest(self) -> dict[str, object]:
        """Private evaluation manifest; never passed into fitting/selection."""
        future = self.future_view()
        return {
            "schema_version": 1,
            "protocol": PROTOCOL,
            "queries": [
                {
                    **_query_public(query),
                    "commitment_sha256": _query_commitment(query, future),
                }
                for query in future.queries
            ],
        }

    def past_conditions(self):
        view = self.past_view()
        for query in view.queries:
            bank = self.dataset.bank(query.bank_id)
            for mask in iter_masks(8):
                yield self._case(bank, query, view, mask)

    def future_conditions(self, mask_indices_by_bank: Mapping[str, tuple[int, ...]]):
        if set(mask_indices_by_bank) != {bank.bank_id for bank in self.dataset.banks}:
            raise ValueError("future masks must cover every and only every bank")
        view = self.future_view()
        for query in view.queries:
            bank = self.dataset.bank(query.bank_id)
            indices = mask_indices_by_bank[bank.bank_id]
            if not indices or len(set(indices)) != len(indices):
                raise ValueError("future mask indices must be unique and nonempty")
            for index in sorted(indices):
                if type(index) is not int or not 0 <= index < 256:
                    raise ValueError("future mask index outside eight-player game")
                yield self._case(bank, query, view, index_to_mask(index, 8))

    def _case(self, bank, query, view, mask):
        memories = tuple(
            memory
            for memory, present in zip(bank.memories, mask, strict=True)
            if present
        )
        return {
            "case_id": f"{query.query_id}:{mask_to_index(mask):03d}",
            "bank": bank,
            "query": query,
            "view": view,
            "mask": mask,
            "messages": build_contract_messages(memories, query, self.output_contract),
            "supported": supported_by(mask, self.minimal_supports[query.query_id]),
            "family": self.query_metadata[query.query_id]["family"],
        }


def _query_public(query: Query) -> dict[str, object]:
    return {
        "query_id": query.query_id,
        "bank_id": query.bank_id,
        "split": query.split.value,
        "template_family": query.template_family,
        "dependency_group": query.dependency_group,
        "text": query.text,
        "options": list(query.options),
    }


def _query_commitment(query: Query, view) -> str:
    payload = [_query_public(query), view.scoring_fingerprint(query)]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _nonce(seed: int, bank_index: int, label: str, count: int) -> list[int]:
    value = int.from_bytes(
        hashlib.sha256(f"{PROTOCOL}:{seed}:{bank_index}:{label}".encode()).digest(),
        "big",
    )
    return random.Random(value).sample(range(100000, 1000000), count)


def generate_prospective_suite(
    *,
    n_banks: int,
    bank_start: int,
    seed: int,
    output_contract: str,
    past_paraphrases: int = 2,
    future_paraphrases: int = 3,
) -> ProspectiveSuite:
    if any(type(value) is not int for value in (n_banks, bank_start, seed)):
        raise ValueError("prospective cohort settings must be integers")
    if n_banks < 1 or bank_start < 400 or bank_start + n_banks > 1000:
        raise ValueError("E4 banks must be fresh and remain in [400,1000)")
    if past_paraphrases != len(PAST_TEMPLATES) or future_paraphrases != len(FUTURE_TEMPLATES):
        raise ValueError("E4 v1 freezes two past and three future paraphrases")
    # Validate before constructing any potentially expensive suite.
    contract_prompt_hash(output_contract)

    banks: list[MemoryBank] = []
    queries: list[Query] = []
    answers: dict[str, str] = {}
    supports: dict[str, tuple[tuple[int, ...], ...]] = {}
    query_meta: dict[str, dict] = {}
    bank_meta: dict[str, dict] = {}
    for bank_index in range(bank_start, bank_start + n_banks):
        bank_id = f"e4-{bank_index}"
        ids = _nonce(seed, bank_index, "identifiers", 20)
        requests = [f"RQ{x}" for x in ids[:4]]
        routes = [f"RT{x}" for x in ids[4:8]]
        middles = [f"RK{x}" for x in ids[8:12]]
        destinations = [f"DS{x}" for x in ids[12:16]]
        distractors = [f"DS{x}" for x in ids[16:18]]

        # Logical roles exactly tile eight items: 1 + 2 + 2 + 3.
        logical_edges = [
            (requests[0], destinations[0]),
            (requests[1], routes[1]),
            (routes[1], destinations[1]),
            (requests[2], destinations[2]),
            (requests[2], destinations[2]),
            (requests[3], routes[3]),
            (routes[3], middles[3]),
            (middles[3], destinations[3]),
        ]
        role_supports = {
            "direct": ((0,),),
            "and2": ((1, 2),),
            "or2": ((3,), (4,)),
            "and3": ((5, 6, 7),),
        }
        order = list(range(8))
        random.Random(_nonce(seed, bank_index, "order", 1)[0]).shuffle(order)
        positions = {logical: position for position, logical in enumerate(order)}
        memories = tuple(
            MemoryItem(
                memory_id=f"{bank_id}-m{position}",
                bank_id=bank_id,
                position=position,
                text=(
                    f"Link {logical_edges[logical][0]} leads to "
                    f"{logical_edges[logical][1]}."
                ),
            )
            for position, logical in enumerate(order)
        )
        banks.append(MemoryBank(bank_id=bank_id, memories=memories))
        options = destinations + distractors + ["UNKNOWN"]
        random.Random(_nonce(seed, bank_index, "options", 1)[0]).shuffle(options)
        bank_meta[bank_id] = {
            "base_bank_id": bank_id,
            "families": list(FAMILIES),
            "shift": SHIFT,
            "record_storage_tokens": [memory.storage_tokens for memory in memories],
            "record_storage_bytes": [memory.storage_bytes for memory in memories],
        }

        for family_index, family in enumerate(FAMILIES):
            mapped_support = tuple(
                tuple(sorted(positions[player] for player in support))
                for support in role_supports[family]
            )
            for split, templates in (
                (QuerySplit.PAST, PAST_TEMPLATES),
                (QuerySplit.FUTURE, FUTURE_TEMPLATES),
            ):
                for template_index, template in enumerate(templates):
                    query_id = (
                        f"{bank_id}-{split.value}-{family}-q{template_index}"
                    )
                    query = Query(
                        query_id=query_id,
                        bank_id=bank_id,
                        split=split,
                        template_family=f"e4-{SHIFT}-{split.value}-v{template_index + 1}",
                        dependency_group=f"{bank_id}-{family}",
                        text=template.format(request=requests[family_index]),
                        options=tuple(options),
                    )
                    queries.append(query)
                    answers[query_id] = destinations[family_index]
                    supports[query_id] = mapped_support
                    query_meta[query_id] = {
                        "base_bank_id": bank_id,
                        "family": family,
                        "split": split.value,
                        "shift": SHIFT,
                        "paraphrase_index": template_index,
                    }

    dataset = ControlledDataset(
        banks=tuple(banks),
        queries=tuple(queries),
        answers=answers,
        version=PROTOCOL,
    )
    return ProspectiveSuite(
        dataset=dataset,
        minimal_supports=MappingProxyType(supports),
        query_metadata=MappingProxyType(query_meta),
        bank_metadata=MappingProxyType(bank_meta),
        output_contract=output_contract,
    )


def symbolic_prospective_controls(suite: ProspectiveSuite) -> dict[str, object]:
    from hibermem.evaluation.scoring import parse_action

    oracle = FactorialOracle()
    counts = {"past": 0, "future": 0}
    for iterator, split in (
        (suite.past_conditions(), "past"),
        (
            suite.future_conditions(
                {bank.bank_id: tuple(range(256)) for bank in suite.dataset.banks}
            ),
            "future",
        ),
    ):
        for case in iterator:
            answer = oracle.generate(case["messages"]).text
            parsed = parse_action(answer, case["query"].options)
            if case["view"].score(case["query"], parsed) != float(case["supported"]):
                raise ValueError(f"prospective symbolic mismatch: {case['case_id']}")
            if not case["supported"] and answer != "UNKNOWN":
                raise ValueError("prospective oracle asserted without support")
            counts[split] += 1
    return {
        "passed": True,
        "complete_game_checks": counts,
        "scope": "engineering grammar/support controls; no future model evidence",
        "historical_test_access": False,
        "support_available_to_policy": False,
    }


__all__ = [
    "FAMILIES",
    "PROTOCOL",
    "SHIFT",
    "FutureQueryCapability",
    "PastQueryCapability",
    "ProspectiveSuite",
    "generate_prospective_suite",
    "symbolic_prospective_controls",
]
