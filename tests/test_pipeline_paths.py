from pathlib import Path

from src.common.config import BRONZE_DIR, GOLD_DIR, SILVER_DIR


def test_expected_directories_are_declared() -> None:
    assert isinstance(BRONZE_DIR, Path)
    assert isinstance(SILVER_DIR, Path)
    assert isinstance(GOLD_DIR, Path)
