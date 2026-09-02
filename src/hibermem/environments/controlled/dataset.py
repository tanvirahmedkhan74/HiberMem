"""Deterministic, capability-split Phase 2 dataset.

The public query records intentionally contain no answer field. Answer keys are
held by split-scoped evaluation views, so discovery code cannot accidentally
score validation or test identifiers.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from enum import Enum
from itertools import permutations
from types import MappingProxyType
from typing import Mapping

from hibermem.memory import MemoryItem


DATASET_VERSION = "phase2-routing-v4"


class QuerySplit(str, Enum):
    DISCOVERY = "discovery"
    VALIDATION = "validation"
    TEST = "test"
    # New prospective protocols use explicit capabilities rather than overloading
    # historical Phase-2 validation/test semantics. Existing datasets are unchanged.
    PAST = "past"
    FUTURE = "future"


@dataclass(frozen=True)
class Query:
    query_id: str
    bank_id: str
    split: QuerySplit
    template_family: str
    dependency_group: str
    text: str
    options: tuple[str, ...]


@dataclass(frozen=True)
class MemoryBank:
    bank_id: str
    memories: tuple[MemoryItem, ...]


class EvaluationView:
    """Split-scoped query and scoring capability."""

    def __init__(self, split: QuerySplit, queries: tuple[Query, ...], answers: Mapping[str, str]):
        if any(query.split is not split for query in queries):
            raise ValueError("an evaluation view cannot mix query splits")
        query_ids = {query.query_id for query in queries}
        if query_ids != set(answers):
            raise ValueError("the answer capability must exactly match its query identifiers")
        self.split = split
        self.queries = queries
        self._queries_by_id = MappingProxyType({query.query_id: query for query in queries})
        self._answers = MappingProxyType(dict(answers))

    def for_bank(self, bank_id: str) -> tuple[Query, ...]:
        return tuple(query for query in self.queries if query.bank_id == bank_id)

    def authorize(self, query: Query) -> None:
        """Validate the complete query before evaluation, including cache hits."""
        if query.split is not self.split or self._queries_by_id.get(query.query_id) != query:
            raise PermissionError(
                f"{self.split.value} view cannot score query {query.query_id!r}"
            )

    def scoring_fingerprint(self, query: Query) -> str:
        self.authorize(query)
        return hashlib.sha256(
            json.dumps([query.query_id, self.split.value, self._answers[query.query_id]]).encode()
        ).hexdigest()

    def score(self, query: Query, parsed_action: str | None) -> float:
        self.authorize(query)
        return float(parsed_action == self._answers[query.query_id])


class ControlledDataset:
    def __init__(
        self,
        *,
        banks: tuple[MemoryBank, ...],
        queries: tuple[Query, ...],
        answers: Mapping[str, str],
        version: str = DATASET_VERSION,
    ) -> None:
        if len({bank.bank_id for bank in banks}) != len(banks):
            raise ValueError("bank identifiers must be unique")
        if len({query.query_id for query in queries}) != len(queries):
            raise ValueError("query identifiers must be unique")
        if set(answers) != {query.query_id for query in queries}:
            raise ValueError("answers must cover every and only every query")
        bank_ids = {bank.bank_id for bank in banks}
        if any(query.bank_id not in bank_ids for query in queries):
            raise ValueError("every query must reference a known bank")
        self.banks = banks
        self.queries = queries
        self.version = version
        self._answers = dict(answers)

    def view(self, split: QuerySplit) -> EvaluationView:
        queries = tuple(query for query in self.queries if query.split is split)
        answers = {query.query_id: self._answers[query.query_id] for query in queries}
        return EvaluationView(split, queries, answers)

    def bank(self, bank_id: str) -> MemoryBank:
        return next(bank for bank in self.banks if bank.bank_id == bank_id)

    def public_manifest(self, *, include_test: bool = False) -> dict[str, object]:
        return {
            "schema_version": 1,
            "dataset_version": self.version,
            "banks": [
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
                }
                for bank in self.banks
            ],
            "queries": [
                {
                    "query_id": query.query_id,
                    "bank_id": query.bank_id,
                    "split": query.split.value,
                    "template_family": query.template_family,
                    "dependency_group": query.dependency_group,
                    "text": query.text,
                    "options": list(query.options),
                }
                for query in self.queries
                if include_test or query.split is not QuerySplit.TEST
            ],
        }

    def sha256(self) -> str:
        encoded = json.dumps(
            self.public_manifest(include_test=True), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


_REQUEST_SUFFIXES = ("P", "Q", "R", "S")
_ROUTE_SUFFIXES = ("A", "B", "C", "D")
_DESTINATION_SUFFIXES = ("K", "L", "M", "N")

_DISCOVERY_FINAL_TEMPLATES = (
    "At which destination does request {request} ultimately reach?",
    "Using the routing records, at which destination does request {request} ultimately reach?",
    "Trace the assignment: at which destination does request {request} ultimately reach?",
    "Resolve the chain and report this: at which destination does request {request} ultimately reach?",
)
_VALIDATION_FINAL_TEMPLATES = (
    "For the validation dispatch, at which destination does request {request} ultimately reach?",
    "Follow both records; at which destination does request {request} ultimately reach?",
)
_TEST_FINAL_TEMPLATES = (
    "For the held-out audit, at which destination does request {request} ultimately reach?",
    "Use only the supplied facts: at which destination does request {request} ultimately reach?",
    "Complete the two-step lookup: at which destination does request {request} ultimately reach?",
    "Give the final location: at which destination does request {request} ultimately reach?",
)


def _tokens(bank_index: int) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    requests = tuple(f"RQ{bank_index:02d}-{suffix}" for suffix in _REQUEST_SUFFIXES)
    route_candidates = [
        candidate
        for candidate in permutations(_ROUTE_SUFFIXES)
        if all(candidate[index] != _ROUTE_SUFFIXES[index] for index in range(4))
    ]
    route_suffixes = random.Random(19_901 + bank_index * 101).choice(route_candidates)
    destination_candidates = [
        candidate
        for candidate in permutations(_DESTINATION_SUFFIXES)
        if all(
            candidate[index] != _DESTINATION_SUFFIXES[index]
            and _DESTINATION_SUFFIXES.index(candidate[index])
            != _ROUTE_SUFFIXES.index(route_suffixes[index])
            for index in range(4)
        )
    ]
    destination_suffixes = random.Random(31_337 + bank_index * 211).choice(
        destination_candidates
    )
    routes = tuple(f"RT{bank_index:02d}-{suffix}" for suffix in route_suffixes)
    destinations = tuple(f"DS{bank_index:02d}-{suffix}" for suffix in destination_suffixes)
    return requests, routes, destinations


def _append_query(
    queries: list[Query],
    answers: dict[str, str],
    *,
    bank_id: str,
    split: QuerySplit,
    template_family: str,
    dependency_group: str,
    text: str,
    options: tuple[str, ...],
    answer: str,
) -> None:
    ordinal = sum(1 for query in queries if query.bank_id == bank_id and query.split is split)
    query_id = f"{bank_id}-{split.value[:1]}-{ordinal:02d}"
    queries.append(
        Query(
            query_id=query_id,
            bank_id=bank_id,
            split=split,
            template_family=template_family,
            dependency_group=dependency_group,
            text=text,
            options=options,
        )
    )
    answers[query_id] = answer


def generate_phase2_dataset(
    n_banks: int = 10, *, bank_start: int = 0
) -> ControlledDataset:
    """Generate independent nonce-token routing environments.

    Each bank has four two-step chains. One discovery/test query per chain asks
    for the first-hop route (individual value), while four ask for the final
    destination (pairwise complementarity). Split-specific surface templates are
    disjoint; dependency groups deliberately recur to test prospective utility.
    """

    if isinstance(n_banks, bool) or not isinstance(n_banks, int) or n_banks < 1:
        raise ValueError("n_banks must be a positive integer")
    if isinstance(bank_start, bool) or not isinstance(bank_start, int) or bank_start < 0:
        raise ValueError("bank_start must be a non-negative integer")
    banks: list[MemoryBank] = []
    queries: list[Query] = []
    answers: dict[str, str] = {}

    for relative_index in range(n_banks):
        bank_index = bank_start + relative_index
        bank_id = f"bank-{bank_index:02d}"
        requests, routes, destinations = _tokens(bank_index)
        memories: list[MemoryItem] = []
        for chain in range(4):
            first_position = chain * 2
            memories.extend(
                (
                    MemoryItem(
                        memory_id=f"{bank_id}-m{first_position}",
                        bank_id=bank_id,
                        position=first_position,
                        text=(
                            f"Request {requests[chain]} is allocated routing code "
                            f"{routes[chain]}."
                        ),
                    ),
                    MemoryItem(
                        memory_id=f"{bank_id}-m{first_position + 1}",
                        bank_id=bank_id,
                        position=first_position + 1,
                        text=(
                            f"Routing code {routes[chain]} directly delivers to "
                            f"{destinations[chain]}."
                        ),
                    ),
                )
            )
        banks.append(MemoryBank(bank_id=bank_id, memories=tuple(memories)))
        route_options = tuple(
            sorted(routes + (f"RT{bank_index:02d}-X", f"RT{bank_index:02d}-Y"))
        ) + ("UNKNOWN",)
        destination_options = tuple(
            sorted(
                destinations + (f"DS{bank_index:02d}-X", f"DS{bank_index:02d}-Y")
            )
        ) + ("UNKNOWN",)

        for chain in range(4):
            dependency = f"{bank_id}-chain-{chain}"
            _append_query(
                queries,
                answers,
                bank_id=bank_id,
                split=QuerySplit.DISCOVERY,
                template_family="discovery-direct-v1",
                dependency_group=dependency,
                text=(
                    "For the discovery ledger, which routing code is allocated to request "
                    f"{requests[chain]}?"
                ),
                options=route_options,
                answer=routes[chain],
            )
            for template_index, template in enumerate(_DISCOVERY_FINAL_TEMPLATES):
                _append_query(
                    queries,
                    answers,
                    bank_id=bank_id,
                    split=QuerySplit.DISCOVERY,
                    template_family=f"discovery-final-v{template_index + 1}",
                    dependency_group=dependency,
                    text=template.format(request=requests[chain]),
                    options=destination_options,
                    answer=destinations[chain],
                )

            if chain < 2:
                _append_query(
                    queries,
                    answers,
                    bank_id=bank_id,
                    split=QuerySplit.VALIDATION,
                    template_family="validation-direct-v1",
                    dependency_group=dependency,
                    text=(
                        "During validation, which routing code is allocated to request "
                        f"{requests[chain]}?"
                    ),
                    options=route_options,
                    answer=routes[chain],
                )
            for template_index, template in enumerate(_VALIDATION_FINAL_TEMPLATES):
                _append_query(
                    queries,
                    answers,
                    bank_id=bank_id,
                    split=QuerySplit.VALIDATION,
                    template_family=f"validation-final-v{template_index + 1}",
                    dependency_group=dependency,
                    text=template.format(request=requests[chain]),
                    options=destination_options,
                    answer=destinations[chain],
                )

            _append_query(
                queries,
                answers,
                bank_id=bank_id,
                split=QuerySplit.TEST,
                template_family="test-direct-v1",
                dependency_group=dependency,
                text=(
                    "For the prospective check, which routing code is allocated to request "
                    f"{requests[chain]}?"
                ),
                options=route_options,
                answer=routes[chain],
            )
            for template_index, template in enumerate(_TEST_FINAL_TEMPLATES):
                _append_query(
                    queries,
                    answers,
                    bank_id=bank_id,
                    split=QuerySplit.TEST,
                    template_family=f"test-final-v{template_index + 1}",
                    dependency_group=dependency,
                    text=template.format(request=requests[chain]),
                    options=destination_options,
                    answer=destinations[chain],
                )

    return ControlledDataset(banks=tuple(banks), queries=tuple(queries), answers=answers)
