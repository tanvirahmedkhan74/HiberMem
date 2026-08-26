"""Locked prompt construction for direct-survivor Phase 2 evaluation."""

from __future__ import annotations

import hashlib

from hibermem.backends.base import Message
from hibermem.memory import MemoryItem

from .dataset import Query


PROMPT_TEMPLATE_VERSION = "phase2-direct-survivors-v3"
SYSTEM_PROMPT = (
    "You solve exact routing lookups using only the external-memory records supplied "
    "by the user. Match identifiers character for character. For a routing-code "
    "question, find the record naming that request and copy its routing code. For a "
    "destination question, first find the request's routing code, then find the record "
    "naming that routing code and copy its destination. Both records are required for "
    "a destination answer. Before answering, verify that the chosen code or destination "
    "appears verbatim in a supplied record that completes the lookup. Never infer an "
    "answer from identifier suffixes or option order. If a required record is absent, "
    "answer UNKNOWN. Never invent a label. Return exactly one token from Allowed answers "
    "and no explanation."
)


def prompt_template_hash() -> str:
    template = (
        PROMPT_TEMPLATE_VERSION
        + "\n"
        + SYSTEM_PROMPT
        + "\nExternal-memory records:\n{MEMORIES}\nTask: {QUESTION}\nAllowed answers: {OPTIONS}"
    )
    return hashlib.sha256(template.encode("utf-8")).hexdigest()


def build_messages(memories: tuple[MemoryItem, ...], query: Query) -> list[Message]:
    if any(memory.bank_id != query.bank_id for memory in memories):
        raise ValueError("all supplied memories must belong to the query bank")
    ordered = tuple(sorted(memories, key=lambda memory: memory.position))
    memory_text = "\n".join(f"M{memory.position}: {memory.text}" for memory in ordered)
    if not memory_text:
        memory_text = "(none)"
    user_prompt = (
        f"External-memory records:\n{memory_text}\n\n"
        f"Task: {query.text}\n"
        f"Allowed answers: {', '.join(query.options)}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
