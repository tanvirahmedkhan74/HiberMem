"""Minimal OpenAI-compatible chat-completions backend."""

from __future__ import annotations

import json
from urllib import request

from .base import GenerationResult, LLMBackend, Message


class OpenAICompatibleBackend(LLMBackend):
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model_id: str,
        model_revision: str = "provider-managed",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_id = model_id
        self.model_revision = model_revision
        self.quantization = "provider-managed"
        self.timeout_seconds = timeout_seconds

    def generate(self, messages: list[Message], **kwargs: object) -> GenerationResult:
        if bool(kwargs.get("do_sample", False)):
            raise ValueError("Phase 2 core generation must be deterministic")
        payload = json.dumps(
            {
                "model": self.model_id,
                "messages": messages,
                "temperature": 0,
                "max_tokens": int(kwargs.get("max_new_tokens", 8)),
            }
        ).encode("utf-8")
        http_request = request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        usage = body.get("usage", {})
        return GenerationResult(
            text=str(body["choices"][0]["message"]["content"]).strip(),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )
