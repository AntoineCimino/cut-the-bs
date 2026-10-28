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


def test_prompt_puts_thesis_section_first_in_all_languages():
    for language in ("English", "French"):
        prompt = synthesis._build_prompt("Invented transcript.", language)
        assert f"in {language}" in prompt
        order = ["Thesis and argument structure", "Overview", "Key points", "Facts and numbers", "Caveats"]
        positions = [prompt.index(title) for title in order]
        assert positions == sorted(positions)
        for needle in ("[verifiable fact]", "[speaker interpretation]", "[unsupported claim]",
                       "Implicit conclusion", "counter-argument"):
            assert needle in prompt


def test_prompt_sent_to_backend_contains_thesis_section(monkeypatch):
    run = Mock(return_value=Mock(stdout="ok"))
    monkeypatch.setattr(synthesis.subprocess, "run", run)
    synthesis.synthesize("Invented transcript.", SynthesisConfig(backend="claude_cli"), "French")
    assert "Thesis and argument structure" in run.call_args.kwargs["input"]
