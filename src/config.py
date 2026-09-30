"""Application configuration loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "config.yaml"
SUPPORTED_BACKENDS = {"claude_cli", "anthropic_api", "fcc_claude"}


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class SynthesisConfig:
    backend: str = "claude_cli"
    model: str = "sonnet"
    timeout_seconds: int = 300


@dataclass(frozen=True)
class AppConfig:
    synthesis: SynthesisConfig


def load_config(path: Path | None = None) -> AppConfig:
    load_dotenv(PROJECT_ROOT / ".env")
    config_path = path or DEFAULT_CONFIG
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"Could not read configuration {config_path}: {exc}") from exc
    section = raw.get("synthesis", {})
    if not isinstance(section, dict):
        raise ConfigError("'synthesis' must be a mapping in the configuration file.")
    backend = os.getenv("SYNTHESIS_BACKEND", section.get("backend", "claude_cli"))
    model = os.getenv("SYNTHESIS_MODEL", section.get("model", "sonnet"))
    timeout_value = os.getenv("SYNTHESIS_TIMEOUT_SECONDS", section.get("timeout_seconds", 300))
    if backend not in SUPPORTED_BACKENDS:
        choices = ", ".join(sorted(SUPPORTED_BACKENDS))
        raise ConfigError(f"Unknown synthesis backend '{backend}'. Choose one of: {choices}.")
    try:
        timeout = int(timeout_value)
    except (TypeError, ValueError) as exc:
        raise ConfigError("SYNTHESIS_TIMEOUT_SECONDS must be an integer.") from exc
    if timeout <= 0:
        raise ConfigError("Synthesis timeout must be greater than zero.")
    return AppConfig(SynthesisConfig(backend, str(model), timeout))
