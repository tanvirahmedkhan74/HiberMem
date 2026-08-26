"""Canonical coalition-mask conversions.

Player ``i`` is represented by bit ``i``. This convention is used by every
exact table and serialized mask in the repository.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from numbers import Integral

Mask = tuple[bool, ...]


def _validate_n_players(n_players: int) -> int:
    if isinstance(n_players, bool) or not isinstance(n_players, Integral):
        raise TypeError("n_players must be an integer")
    result = int(n_players)
    if result < 0:
        raise ValueError("n_players must be non-negative")
    return result


def normalize_mask(mask: Sequence[bool | int], n_players: int | None = None) -> Mask:
    """Return a validated immutable mask."""

    normalized: list[bool] = []
    for value in mask:
        if isinstance(value, bool):
            normalized.append(value)
        elif isinstance(value, Integral) and int(value) in (0, 1):
            normalized.append(bool(value))
        else:
            raise ValueError("mask values must be booleans or integers 0/1")
    result = tuple(normalized)
    if n_players is not None and len(result) != _validate_n_players(n_players):
        raise ValueError(f"expected mask length {n_players}, got {len(result)}")
    return result


def coalition_to_mask(coalition: Iterable[int], n_players: int) -> Mask:
    """Convert player identifiers to a canonical boolean mask."""

    n_players = _validate_n_players(n_players)
    result = [False] * n_players
    for player in coalition:
        if isinstance(player, bool) or not isinstance(player, Integral):
            raise TypeError("player identifiers must be integers")
        player = int(player)
        if not 0 <= player < n_players:
            raise ValueError(f"player {player} is outside [0, {n_players})")
        if result[player]:
            raise ValueError(f"duplicate player {player}")
        result[player] = True
    return tuple(result)


def mask_to_coalition(mask: Sequence[bool | int]) -> tuple[int, ...]:
    """Return the sorted player identifiers present in ``mask``."""

    return tuple(index for index, present in enumerate(normalize_mask(mask)) if present)


def mask_to_index(mask: Sequence[bool | int]) -> int:
    """Encode a mask as an integer with player ``i`` at bit ``i``."""

    result = 0
    for player, present in enumerate(normalize_mask(mask)):
        if present:
            result |= 1 << player
    return result


def index_to_mask(index: int, n_players: int) -> Mask:
    """Decode an integer coalition index."""

    n_players = _validate_n_players(n_players)
    if isinstance(index, bool) or not isinstance(index, Integral):
        raise TypeError("index must be an integer")
    index = int(index)
    if not 0 <= index < (1 << n_players):
        raise ValueError(f"index must be in [0, {1 << n_players})")
    return tuple(bool(index & (1 << player)) for player in range(n_players))


def iter_masks(n_players: int) -> Iterator[Mask]:
    """Yield all masks in deterministic integer-index order."""

    n_players = _validate_n_players(n_players)
    for index in range(1 << n_players):
        yield index_to_mask(index, n_players)


def serialize_mask(mask: Sequence[bool | int]) -> str:
    """Serialize a mask using a versioned, self-describing representation."""

    normalized = normalize_mask(mask)
    return f"v1:{len(normalized)}:{mask_to_index(normalized):x}"


def deserialize_mask(serialized: str) -> Mask:
    """Deserialize a mask and reject malformed or out-of-range encodings."""

    if not isinstance(serialized, str):
        raise TypeError("serialized mask must be a string")
    parts = serialized.split(":")
    if len(parts) != 3 or parts[0] != "v1":
        raise ValueError("unsupported mask serialization")
    try:
        n_players = int(parts[1], 10)
        index = int(parts[2], 16)
    except ValueError as error:
        raise ValueError("malformed mask serialization") from error
    if str(n_players) != parts[1] or n_players < 0 or not parts[2]:
        raise ValueError("non-canonical mask serialization")
    return index_to_mask(index, n_players)
