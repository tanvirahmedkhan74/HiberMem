"""Unit tests must not download or initialize real language models."""

import pytest

from hibermem.backends import HFLocalBackend


@pytest.fixture(autouse=True)
def block_real_model_loading(monkeypatch):
    # Patch the class constructor, not just one runner's imported factory alias.
    # This fails even if weights are already cached and no network is needed.
    def forbidden(*args, **kwargs):
        pytest.fail("Real model loading is forbidden in unit tests; use a mock backend")

    monkeypatch.setattr(HFLocalBackend, "__init__", forbidden)
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
