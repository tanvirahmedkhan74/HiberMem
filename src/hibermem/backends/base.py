"""Common LLM backend contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypedDict


class Message(TypedDict):
    role: str
    content: str


@dataclass(frozen=True)
class GenerationResult:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    # Optional immutable-by-convention evidence for audited experiment runners.
    # Legacy cache/scoring consumers retain their existing behavior.
    trace: dict[str, object] | None = None


class LLMBackend(ABC):
    """Model-family-independent generation interface."""

    model_id: str
    model_revision: str
    quantization: str

    @abstractmethod
    def generate(self, messages: list[Message], **kwargs: object) -> GenerationResult:
        """Generate one result from a chat-style prompt."""

    def provenance(self) -> dict[str, str]:
        return {
            "backend": type(self).__name__,
            "model_id": self.model_id,
            "model_revision": self.model_revision,
            "quantization": self.quantization,
        }
