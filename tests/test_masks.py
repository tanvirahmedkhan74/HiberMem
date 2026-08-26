import pytest

from hibermem.coalition.masks import (
    coalition_to_mask,
    deserialize_mask,
    index_to_mask,
    iter_masks,
    mask_to_coalition,
    mask_to_index,
    serialize_mask,
)


def test_mask_roundtrip() -> None:
    for n_players in range(0, 9):
        for mask in iter_masks(n_players):
            assert index_to_mask(mask_to_index(mask), n_players) == mask
            assert deserialize_mask(serialize_mask(mask)) == mask
            assert coalition_to_mask(mask_to_coalition(mask), n_players) == mask


def test_mask_enumeration_is_deterministic() -> None:
    first = list(iter_masks(5))
    second = list(iter_masks(5))
    assert first == second
    assert [mask_to_index(mask) for mask in first] == list(range(32))


@pytest.mark.parametrize("serialized", ["", "v2:3:1", "v1:-1:0", "v1:2:4", "v1:03:1"])
def test_malformed_serialization_is_rejected(serialized: str) -> None:
    with pytest.raises(ValueError):
        deserialize_mask(serialized)
