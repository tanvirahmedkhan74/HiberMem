"""Transparent payload accounting for frozen retention comparisons."""

from __future__ import annotations

from collections.abc import Iterable

from hibermem.coalition.masks import Mask, normalize_mask
from hibermem.environments.controlled.dataset import MemoryBank


def retained_payload_cost(bank: MemoryBank, mask: Mask) -> dict[str, int]:
    normalized = normalize_mask(mask, len(bank.memories))
    retained = [
        memory
        for memory, present in zip(bank.memories, normalized, strict=True)
        if present
    ]
    return {
        "keep_count": len(retained),
        "payload_bytes": sum(memory.storage_bytes for memory in retained),
        "payload_whitespace_tokens": sum(memory.storage_tokens for memory in retained),
    }


def equal_length_bank_audit(bank: MemoryBank) -> dict[str, object]:
    byte_costs = [memory.storage_bytes for memory in bank.memories]
    token_costs = [memory.storage_tokens for memory in bank.memories]
    return {
        "bank_id": bank.bank_id,
        "record_payload_bytes": byte_costs,
        "record_whitespace_tokens": token_costs,
        "equal_payload_bytes": len(set(byte_costs)) == 1,
        "equal_whitespace_tokens": len(set(token_costs)) == 1,
    }


def validate_equal_cardinality_costs(
    bank: MemoryBank, masks: Iterable[Mask], keep_count: int
) -> list[dict[str, int]]:
    costs = [retained_payload_cost(bank, mask) for mask in masks]
    if not costs or any(cost["keep_count"] != keep_count for cost in costs):
        raise ValueError("retention masks do not share the requested cardinality")
    audit = equal_length_bank_audit(bank)
    if not audit["equal_payload_bytes"] or not audit["equal_whitespace_tokens"]:
        raise ValueError(
            "E4 v1 cardinality comparison requires equal-length memory records"
        )
    if len({(cost["payload_bytes"], cost["payload_whitespace_tokens"]) for cost in costs}) != 1:
        raise ValueError("equal-cardinality E4 masks have unequal payload costs")
    return costs


__all__ = [
    "equal_length_bank_audit",
    "retained_payload_cost",
    "validate_equal_cardinality_costs",
]
