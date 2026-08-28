import pytest

from scripts.verify_kaggle_environment import verify


def test_kaggle_environment_rejects_non_hibermem_repository_first(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "state-geometry-video"\n', encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="wrong GitHub repository"):
        verify(tmp_path)
