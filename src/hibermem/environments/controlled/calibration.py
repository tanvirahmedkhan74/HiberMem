"""Development-only v2 routing screen, with paired counterfactual worlds.

No test queries or confirmation banks are generated. World variants are repeated
conditions of a base bank, never independent statistical replicates.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass

from hibermem.coalition.masks import Mask, serialize_mask
from hibermem.memory import MemoryItem
from .dataset import ControlledDataset, MemoryBank, Query, QuerySplit
from .prompts import build_messages

CALIBRATION_VERSION = "phase2r-counterfactual-routing-v2"
DEVELOPMENT_RANGE = (300, 400)
RESERVED_CONFIRMATION_RANGE = (400, 500)


@dataclass(frozen=True)
class CalibrationCase:
    base_bank_id: str
    query: Query
    mask: Mask
    condition: str
    kind: str
    supported: bool
    counterfactual_id: str | None = None
    world: str = "base"

    @property
    def case_id(self) -> str:
        return f"{self.query.query_id}:{self.condition}:{self.counterfactual_id or 'none'}"


@dataclass(frozen=True)
class CalibrationSuite:
    dataset: ControlledDataset
    cases: tuple[CalibrationCase, ...]

    def manifest(self) -> dict[str, object]:
        return {
            "dataset": self.dataset.public_manifest(),
            "cases": [
                {"case_id": c.case_id, "base_bank_id": c.base_bank_id,
                 "query_id": c.query.query_id, "mask": serialize_mask(c.mask),
                 "condition": c.condition, "kind": c.kind, "supported": c.supported,
                 "counterfactual_id": c.counterfactual_id, "world": c.world}
                for c in self.cases
            ],
        }

    def sha256(self) -> str:
        return hashlib.sha256(json.dumps(self.manifest(), sort_keys=True).encode()).hexdigest()


def generate_calibration_v2(
    n_banks: int = 10, *, bank_start: int = 300, seed: int = 20260830
) -> CalibrationSuite:
    if n_banks < 1 or bank_start < DEVELOPMENT_RANGE[0] or bank_start + n_banks > DEVELOPMENT_RANGE[1]:
        raise ValueError("v2 development banks must stay inside [300, 400); confirmation is reserved")
    banks: list[MemoryBank] = []
    queries: list[Query] = []
    answers: dict[str, str] = {}
    cases: list[CalibrationCase] = []

    def mask(*positions: int) -> Mask:
        return tuple(i in positions for i in range(8))

    for bank_index in range(bank_start, bank_start + n_banks):
        rng = random.Random(seed + bank_index * 104729)
        base_id = f"dev-{bank_index:03d}"
        # Independent uniform identifiers; no derangements, alphabet mappings,
        # suffix restrictions, sorted answer order, or chain-dependent positions.
        labels = rng.sample(range(100000, 999999), 20)
        requests = [f"RQ{number}" for number in labels[:4]]
        routes = [f"RT{number}" for number in labels[4:8]]
        destinations = [f"DS{number}" for number in labels[8:12]]
        route_options = [*routes, *(f"RT{x}" for x in labels[12:16]), "UNKNOWN"]
        destination_options = [*destinations, *(f"DS{x}" for x in labels[16:20]), "UNKNOWN"]
        rng.shuffle(route_options)
        rng.shuffle(destination_options)
        positions = list(range(8))
        rng.shuffle(positions)
        first = [positions[2 * i] for i in range(4)]
        second = [positions[2 * i + 1] for i in range(4)]
        texts = [""] * 8
        for chain in range(4):
            texts[first[chain]] = f"Request {requests[chain]} is allocated routing code {routes[chain]}."
            texts[second[chain]] = f"Routing code {routes[chain]} directly delivers to {destinations[chain]}."

        def add_bank(world_id: str, world_texts: list[str]) -> MemoryBank:
            bank = MemoryBank(world_id, tuple(
                MemoryItem(f"{world_id}-m{i}", world_id, i, text)
                for i, text in enumerate(world_texts)
            ))
            banks.append(bank)
            return bank

        base_bank = add_bank(f"{base_id}-base", texts)

        def add_query(bank: MemoryBank, chain: int, template: int, kind: str, answer: str) -> Query:
            # Prefixes are public development families, not final-test material.
            prefix = ("", "Use the supplied ledger. ", "Check the records carefully. ")[template]
            text = (f"Which routing code is allocated to request {requests[chain]}?" if kind == "direct"
                    else f"At which destination does request {requests[chain]} ultimately reach?")
            query = Query(
                f"{bank.bank_id}-{kind}-{chain}-{template}", bank.bank_id,
                QuerySplit.DISCOVERY if template < 2 else QuerySplit.VALIDATION,
                f"dev-{kind}-{template}", f"{base_id}-chain-{chain}", prefix + text,
                tuple(route_options if kind == "direct" else destination_options),
            )
            queries.append(query)
            answers[query.query_id] = answer
            return query

        for chain in range(4):
            alternate = (chain + 1) % 4
            first_texts, second_texts = list(texts), list(texts)
            first_texts[first[chain]] = (
                f"Request {requests[chain]} is allocated routing code {routes[alternate]}."
            )
            second_texts[second[chain]] = (
                f"Routing code {routes[chain]} directly delivers to {destinations[alternate]}."
            )
            variants = {
                "first": add_bank(f"{base_id}-first-{chain}", first_texts),
                "second": add_bank(f"{base_id}-second-{chain}", second_texts),
            }
            for template in range(3):
                direct = add_query(base_bank, chain, template, "direct", routes[chain])
                final = add_query(base_bank, chain, template, "two_hop", destinations[chain])
                for condition, coalition, supported in (
                    ("full", mask(*range(8)), True), ("empty", mask(), False),
                    ("direct_minimal", mask(first[chain]), True),
                ):
                    cases.append(CalibrationCase(base_id, direct, coalition, condition, "direct", supported))
                for condition, coalition, supported in (
                    ("full", mask(*range(8)), True), ("empty", mask(), False),
                    ("pair_only", mask(first[chain], second[chain]), True),
                    ("missing_first_minimal", mask(second[chain]), False),
                    ("missing_second_minimal", mask(first[chain]), False),
                    ("missing_first_context", mask(*(i for i in range(8) if i != first[chain])), False),
                    ("missing_second_context", mask(*(i for i in range(8) if i != second[chain])), False),
                ):
                    cases.append(CalibrationCase(base_id, final, coalition, condition, "two_hop", supported))
                for direction, removed in (("first", first[chain]), ("second", second[chain])):
                    variant = add_query(variants[direction], chain, template, "two_hop", destinations[alternate])
                    pair_id = f"{base_id}-{chain}-{template}-{direction}"
                    for world, query in (("base", final), ("alternate", variant)):
                        for condition, coalition, supported in (
                            ("cf_full", mask(*range(8)), True),
                            ("cf_missing", mask(*(i for i in range(8) if i != removed)), False),
                        ):
                            cases.append(CalibrationCase(base_id, query, coalition, condition,
                                                         "two_hop", supported, pair_id, world))

    dataset = ControlledDataset(banks=tuple(banks), queries=tuple(queries), answers=answers,
                                version=CALIBRATION_VERSION)
    suite = CalibrationSuite(dataset, tuple(cases))
    validate_counterfactual_pairs(suite)
    return suite


def validate_counterfactual_pairs(suite: CalibrationSuite) -> None:
    groups: dict[str, list[CalibrationCase]] = {}
    for case in suite.cases:
        if case.condition == "cf_missing":
            groups.setdefault(str(case.counterfactual_id), []).append(case)
    for pair in groups.values():
        if len(pair) != 2:
            raise ValueError("counterfactual groups require two worlds")
        prompts = []
        scores = []
        for case in pair:
            bank = suite.dataset.bank(case.query.bank_id)
            prompts.append(build_messages(tuple(m for m, keep in zip(bank.memories, case.mask) if keep), case.query))
            view = suite.dataset.view(case.query.split)
            scores.append(tuple(view.score(case.query, answer) for answer in case.query.options))
        if prompts[0] != prompts[1] or scores[0] == scores[1]:
            raise ValueError("paired incomplete evidence must be identical with different correct answers")
