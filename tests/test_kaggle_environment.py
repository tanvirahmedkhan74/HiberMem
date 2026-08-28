import pytest

from scripts.verify_kaggle_environment import configured_min_free_storage_gib, verify


def test_kaggle_environment_rejects_non_hibermem_repository_first(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "state-geometry-video"\n', encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="wrong GitHub repository"):
        verify(tmp_path)


def test_kaggle_environment_storage_override_must_be_positive(monkeypatch) -> None:
    monkeypatch.setenv("HIBERMEM_MIN_FREE_STORAGE_GIB", "0")

    with pytest.raises(RuntimeError, match="positive number"):
        configured_min_free_storage_gib()
