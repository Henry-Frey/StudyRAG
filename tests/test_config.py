"""Tests for Settings config."""
from src.config import Settings


def test_defaults():
    s = Settings()
    assert s.app_name == "StudyRAG"
    assert s.default_top_k == 5
    assert 0 < s.score_threshold < 1


def test_env_override(monkeypatch):
    monkeypatch.setenv("STUDYRAG_DEFAULT_TOP_K", "10")
    s = Settings()
    assert s.default_top_k == 10
