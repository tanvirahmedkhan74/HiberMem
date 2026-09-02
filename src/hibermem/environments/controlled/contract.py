"""Fresh development-only output-contract and grounding diagnostics.

This module deliberately wraps, rather than mutates, the validated E3 factorial
generator. Contract variants change only rendering/instruction wording. Structural
support, answers, banks, worlds, and coalition masks remain paired.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from hibermem.coalition.masks import iter_masks, mask_to_index
from hibermem.memory import MemoryItem

from .dataset import Query, QuerySplit
from .factorial import (
    FactorialOracle,
    FactorialSuite,
    SYSTEM_PROMPT as E3_SYSTEM_PROMPT,
    generate_factorial_suite,
    supported_by,
)


PROTOCOL = "phase2r-output-contract-v1"
CONTRACTS = ("current_v1", "answer_slot_v1")

ANSWER_SLOT_SYSTEM_PROMPT = (
    E3_SYSTEM_PROMPT
    + " Perform any path traversal silently. Do not print the path, record names, "
      "punctuation, or commentary. Your entire response must be exactly one Allowed "
      "answers label."
)


def contract_system_prompt(contract: str) -> str:
    if contract == "current_v1":
        return E3_SYSTEM_PROMPT
    if contract == "answer_slot_v1":
        return ANSWER_SLOT_SYSTEM_PROMPT
    raise ValueError(f"unknown output contract: {contract}")


def contract_prompt_hash(contract: str) -> str:
    template = (
        PROTOCOL
        + "\n"
        + contract
        + "\n"
        + contract_system_prompt(contract)
        + "\nExternal-memory records:\n{records}\n\nTask: {query}\n"
          "Allowed answers: {options}{answer_slot}"
    )
    return hashlib.sha256(template.encode("utf-8")).hexdigest()


def build_contract_messages(
    memories: tuple[MemoryItem, ...], query: Query, contract: str
) -> list[dict[str, str]]:
    if any(memory.bank_id != query.bank_id for memory in memories):
        raise ValueError("contract prompt cannot mix memory banks")
    ordered = tuple(sorted(memories, key=lambda memory: memory.position))
    records = "\n".join(f"M{m.position}: {m.text}" for m in ordered) or "(none)"
    answer_slot = "\nAnswer (one allowed label only):" if contract == "answer_slot_v1" else ""
    return [
        {"role": "system", "content": contract_system_prompt(contract)},
        {
            "role": "user",
            "content": (
                f"External-memory records:\n{records}\n\n"
                f"Task: {query.text}\nAllowed answers: {', '.join(query.options)}"
                f"{answer_slot}"
            ),
        },
    ]


@dataclass(frozen=True)
class ContractSuite:
    base: FactorialSuite
    contracts: tuple[str, ...]

    def manifest(self) -> dict[str, object]:
        base_manifest = self.base.manifest()
        planned = int(base_manifest["planned_conditions"]) * len(self.contracts)
        return {
            "schema_version": 1,
            "protocol": PROTOCOL,
            "scope": "development_only_output_contract",
            "contracts": list(self.contracts),
            "contract_prompt_sha256": {
                contract: contract_prompt_hash(contract) for contract in self.contracts
            },
            "base_factorial_manifest": base_manifest,
            "planned_conditions": planned,
            "independent_base_banks": base_manifest["independent_base_banks"],
            "paired_design": (
                "contracts share every bank/query/world/support/mask; variants are not "
                "independent banks"
            ),
            "scientific_gate_eligible": False,
            "future_queries_evaluated": 0,
        }

    def conditions(self):
        view = self.base.dataset.view(QuerySplit.DISCOVERY)
        for contract in self.contracts:
            for query in self.base.dataset.queries:
                bank = self.base.dataset.bank(query.bank_id)
                for mask in iter_masks(8):
                    memories = tuple(
                        memory
                        for memory, present in zip(bank.memories, mask, strict=True)
                        if present
                    )
                    yield {
                        "case_id": (
                            f"{contract}:{query.query_id}:{mask_to_index(mask):03d}"
                        ),
                        "contract": contract,
                        "bank": bank,
                        "query": query,
                        "view": view,
                        "mask": mask,
                        "messages": build_contract_messages(memories, query, contract),
                        "supported": supported_by(
                            mask, self.base.minimal_supports[query.query_id]
                        ),
                    }


def generate_contract_suite(
    *,
    n_banks: int,
    bank_start: int,
    seed: int,
    families: list[str],
    overlap_levels: list[str],
    worlds: list[str],
    contracts: list[str],
) -> ContractSuite:
    if not contracts or any(c not in CONTRACTS for c in contracts):
        raise ValueError("unknown or empty output-contract matrix")
    if len(set(contracts)) != len(contracts):
        raise ValueError("output contracts must be unique")
    if any(f not in ("and2", "and3") for f in families):
        raise ValueError("E3c is restricted to the unresolved AND2/AND3 families")
    if bank_start < 350:
        raise ValueError("E3c must use fresh factorial development banks >= 350")
    base = generate_factorial_suite(
        n_banks=n_banks,
        bank_start=bank_start,
        seed=seed,
        families=families,
        overlap_levels=overlap_levels,
        worlds=worlds,
        variants=["original"],
    )
    return ContractSuite(base=base, contracts=tuple(contracts))


def symbolic_contract_controls(suite: ContractSuite) -> dict[str, object]:
    oracle = FactorialOracle()
    from hibermem.evaluation.scoring import parse_action

    counts = {contract: 0 for contract in suite.contracts}
    for case in suite.conditions():
        answer = oracle.generate(case["messages"]).text
        parsed = parse_action(answer, case["query"].options)
        reward = case["view"].score(case["query"], parsed)
        if reward != float(case["supported"]):
            raise ValueError(f"contract symbolic control failed: {case['case_id']}")
        if not case["supported"] and answer != "UNKNOWN":
            raise ValueError("symbolic contract oracle asserted without support")
        counts[case["contract"]] += 1
    return {
        "passed": True,
        "conditions_by_contract": counts,
        "scope": "engineering grammar/support control; no model qualification",
        "contract_intervention": "rendering/instruction only; structural cases paired",
    }


__all__ = [
    "CONTRACTS",
    "PROTOCOL",
    "ContractSuite",
    "build_contract_messages",
    "contract_prompt_hash",
    "contract_system_prompt",
    "generate_contract_suite",
    "symbolic_contract_controls",
]
