"""Tests for the StudyRAG CLI."""
import json
from unittest.mock import patch, MagicMock
import pytest
from src.cli import chat


class MockArgs:
    url = "http://localhost:8000"
    query = "Was ist Overfitting?"
    agent = "explainer"


def test_chat_prints_answer(capsys):
    response_data = {"agent_name": "Erklaerer", "answer": "Overfitting tritt auf..."}
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = json.dumps(response_data).encode()

    with patch("urllib.request.urlopen", return_value=mock_resp):
        chat(MockArgs())

    captured = capsys.readouterr()
    assert "Overfitting" in captured.out
