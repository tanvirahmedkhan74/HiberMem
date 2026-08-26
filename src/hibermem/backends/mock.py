"""Deterministic controlled-environment backend for tests and smoke runs."""

from __future__ import annotations

import re

from .base import GenerationResult, LLMBackend, Message


_ASSIGNMENT = re.compile(r"Request ([A-Z0-9-]+) is allocated routing code ([A-Z0-9-]+)\.")
_DESTINATION = re.compile(
    r"Routing code ([A-Z0-9-]+) directly delivers to ([A-Z0-9-]+)\."
)
_DIRECT_QUERY = re.compile(r"routing code is allocated to request ([A-Z0-9-]+)\?", re.I)
_FINAL_QUERY = re.compile(r"destination does request ([A-Z0-9-]+) ultimately reach\?", re.I)


class MockBackend(LLMBackend):
    """A prompt-reading oracle, never a source of scientific LLM evidence."""

    model_id = "hibermem/mock-controlled-v1"
    model_revision = "1"
    quantization = "none"

    def generate(self, messages: list[Message], **kwargs: object) -> GenerationResult:
        del kwargs
        prompt = "\n".join(message["content"] for message in messages)
        assignments = dict(_ASSIGNMENT.findall(prompt))
        destinations = dict(_DESTINATION.findall(prompt))

        direct = _DIRECT_QUERY.search(prompt)
        final = _FINAL_QUERY.search(prompt)
        answer = "UNKNOWN"
        if direct:
            answer = assignments.get(direct.group(1), "UNKNOWN")
        elif final:
            route = assignments.get(final.group(1))
            if route is not None:
                answer = destinations.get(route, "UNKNOWN")

        return GenerationResult(
            text=answer,
            input_tokens=len(prompt.split()),
            output_tokens=1,
        )
