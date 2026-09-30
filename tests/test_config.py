from pathlib import Path

import pytest

from config import ConfigError, load_config


def test_environment_selects_backend(tmp_path: Path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("synthesis:\n  backend: claude_cli\n", encoding="utf-8")
    monkeypatch.setenv("SYNTHESIS_BACKEND", "fcc_claude")
    assert load_config(config_file).synthesis.backend == "fcc_claude"


def test_unknown_backend_is_rejected(tmp_path: Path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("synthesis:\n  backend: imaginary\n", encoding="utf-8")
    monkeypatch.delenv("SYNTHESIS_BACKEND", raising=False)
    with pytest.raises(ConfigError, match="Unknown synthesis backend"):
        load_config(config_file)
