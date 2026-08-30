import os

import pytest

from hibermem.backends import HFLocalBackend, MockBackend
from hibermem.experiments.phase2 import make_backend


@pytest.mark.parametrize("via_factory", [False, True], ids=["direct", "factory-alias"])
def test_real_model_guard_fails_before_loading(via_factory):
    config = {"model_id": "must-not-download", "model_revision": "a" * 40}
    with pytest.raises(pytest.fail.Exception, match="Real model loading is forbidden"):
        if via_factory:
            make_backend({"type": "hf_local", **config})
        else:
            HFLocalBackend(**config)


def test_unit_test_guard_allows_mock_and_sets_offline_environment():
    assert isinstance(make_backend({"type": "mock"}), MockBackend)
    assert os.environ["HF_HUB_OFFLINE"] == "1"
    assert os.environ["TRANSFORMERS_OFFLINE"] == "1"
