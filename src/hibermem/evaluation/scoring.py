"""Strict finite-action parsing for controlled LLM outputs."""

from __future__ import annotations

import re
from collections.abc import Iterable


def parse_action(raw_output: str, options: Iterable[str]) -> str | None:
    allowed = tuple(options)
    normalized = raw_output.strip().upper()
    exact = {option.upper(): option for option in allowed}
    if normalized in exact:
        return exact[normalized]

    found: list[str] = []
    for option in allowed:
        if re.search(rf"(?<![A-Z0-9-]){re.escape(option.upper())}(?![A-Z0-9-])", normalized):
            found.append(option)
    unique = tuple(dict.fromkeys(found))
    return unique[0] if len(unique) == 1 else None
