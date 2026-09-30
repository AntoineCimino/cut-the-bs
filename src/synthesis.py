"""Configurable synthesis backends."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable

from config import SynthesisConfig

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "synthesis.md"


class SynthesisError(RuntimeError):
    pass


def _build_prompt(transcript: str, output_language: str) -> str:
    try:
        template = PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise SynthesisError(f"Could not load synthesis prompt: {exc}") from exc
    return (
        f"{template}\n\nWrite the entire output in {output_language}.\n\n"
        f"<transcript>\n{transcript}\n</transcript>"
    )


def _run_cli(command: str, prompt: str, config: SynthesisConfig) -> str:
    args = [command, "-p"]
    if config.model:
        args.extend(["--model", config.model])
    try:
        result = subprocess.run(
            args, input=prompt, capture_output=True, text=True, check=True, timeout=config.timeout_seconds
        )
    except FileNotFoundError as exc:
        raise SynthesisError(f"The '{command}' executable was not found. Install it or select another backend.") from exc
    except subprocess.TimeoutExpired as exc:
        raise SynthesisError(f"The {command} backend timed out.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "unknown CLI error").strip()
        raise SynthesisError(f"The {command} backend failed: {detail}") from exc
    output = result.stdout.strip()
    if not output:
        raise SynthesisError(f"The {command} backend returned an empty response.")
    return output


def _claude_cli(prompt: str, config: SynthesisConfig) -> str:
    return _run_cli("claude", prompt, config)


def _fcc_claude(prompt: str, config: SynthesisConfig) -> str:
    return _run_cli("fcc-claude", prompt, config)


def _anthropic_api(prompt: str, config: SynthesisConfig) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SynthesisError("ANTHROPIC_API_KEY is required when synthesis.backend is anthropic_api.")
    try:
        from anthropic import Anthropic

        response = Anthropic(api_key=api_key).messages.create(
            model=config.model, max_tokens=4096, messages=[{"role": "user", "content": prompt}]
        )
        output = "".join(block.text for block in response.content if getattr(block, "type", "") == "text").strip()
    except Exception as exc:
        raise SynthesisError(f"The Anthropic API backend failed: {exc}") from exc
    if not output:
        raise SynthesisError("The Anthropic API backend returned an empty response.")
    return output


BACKENDS: dict[str, Callable[[str, SynthesisConfig], str]] = {
    "claude_cli": _claude_cli,
    "anthropic_api": _anthropic_api,
    "fcc_claude": _fcc_claude,
}


def synthesize(transcript: str, config: SynthesisConfig, output_language: str = "English") -> str:
    backend = BACKENDS.get(config.backend)
    if backend is None:
        raise SynthesisError(f"Unsupported synthesis backend: {config.backend}")
    return backend(_build_prompt(transcript, output_language), config)
