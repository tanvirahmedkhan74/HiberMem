"""Core memory records shared by controlled environments and experiments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryItem:
    """One immutable, directly deliverable external-memory item."""

    memory_id: str
    bank_id: str
    position: int
    text: str

    def __post_init__(self) -> None:
        if not self.memory_id or not self.bank_id or not self.text.strip():
            raise ValueError("memory_id, bank_id, and text must be non-empty")
        if self.position < 0:
            raise ValueError("position must be non-negative")

    @property
    def storage_bytes(self) -> int:
        return len(self.text.encode("utf-8"))

    @property
    def storage_tokens(self) -> int:
        """Locked Phase 2 accounting proxy; real tokenizer counts are also logged."""

        return len(self.text.split())
