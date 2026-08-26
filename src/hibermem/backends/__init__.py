"""Backend-independent deterministic text generation."""

from .base import GenerationResult, LLMBackend, Message
from .hf_local import HFLocalBackend
from .mock import MockBackend
from .openai_compatible import OpenAICompatibleBackend

__all__ = [
    "GenerationResult",
    "HFLocalBackend",
    "LLMBackend",
    "Message",
    "MockBackend",
    "OpenAICompatibleBackend",
]
