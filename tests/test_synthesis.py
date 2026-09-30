from unittest.mock import Mock

import pytest

import synthesis
from config import SynthesisConfig


@pytest.mark.parametrize(("backend", "command"), [("claude_cli", "claude"), ("fcc_claude", "fcc-claude")])
def test_cli_backend_selection(monkeypatch, backend, command):
    run = Mock(return_value=Mock(stdout="Neutral synthetic summary."))
    monkeypatch.setattr(synthesis.subprocess, "run", run)
    result = synthesis.synthesize("Invented transcript.", SynthesisConfig(backend=backend, model="test-model"))
    assert result == "Neutral synthetic summary."
    assert run.call_args.args[0][0] == command


def test_missing_cli_has_clear_error(monkeypatch):
    monkeypatch.setattr(synthesis.subprocess, "run", Mock(side_effect=FileNotFoundError()))
    with pytest.raises(synthesis.SynthesisError, match="executable was not found"):
        synthesis.synthesize("Invented transcript.", SynthesisConfig(backend="claude_cli"))


def test_anthropic_backend_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(synthesis.SynthesisError, match="ANTHROPIC_API_KEY is required"):
        synthesis.synthesize("Invented transcript.", SynthesisConfig(backend="anthropic_api"))
