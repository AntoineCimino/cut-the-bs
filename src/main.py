"""Command-line entry point for Cut the BS."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path

from config import ConfigError, load_config
from pdf_export import export_pdf
from synthesis import SynthesisError, synthesize
from transcript import TranscriptError, extract_youtube_id, fetch_video

# ISO 639-1 code -> English language name, for the small set YouTube auto-captions commonly use.
# Unknown codes fall back to the raw code itself.
LANGUAGE_NAMES = {
    "en": "English", "fr": "French", "es": "Spanish", "de": "German", "it": "Italian",
    "pt": "Portuguese", "nl": "Dutch", "ja": "Japanese", "ko": "Korean", "zh": "Chinese",
    "ru": "Russian", "ar": "Arabic", "hi": "Hindi",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Turn a YouTube transcript into a factual PDF summary.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("-o", "--output", type=Path, default=Path("output/summary.pdf"), help="Output PDF path (default: output/summary.pdf)")
    parser.add_argument("--config", type=Path, default=None, help="Configuration file")
    parser.add_argument("--log-dir", type=Path, default=Path("logs"), help="Local run log folder (default: logs/)")
    parser.add_argument("--lang", default=None, help="Comma-separated output languages, overriding config (e.g. en,fr)")
    parser.add_argument("--no-log", action="store_true", help="Do not persist the run under the log folder")
    return parser


def save_run_log(log_dir: Path, url: str, video, synthesis, syntheses: dict[str, str], now: datetime | None = None) -> Path:
    """Write one run to <log_dir>/<date>_<video_id>[_HHMMSS]/ and return that folder."""
    now = now or datetime.now()
    try:
        video_id = extract_youtube_id(url)
    except TranscriptError:
        video_id = hashlib.sha256(url.encode()).hexdigest()[:10]
    folder = log_dir / f"{now:%Y-%m-%d}_{video_id}"
    if folder.exists():
        folder = log_dir / f"{now:%Y-%m-%d}_{video_id}_{now:%H%M%S%f}"
    folder.mkdir(parents=True)
    meta = {"video_id": video_id, "url": url, "title": video.title, "date": now.isoformat(timespec="seconds"),
            "backend": synthesis.backend, "model": synthesis.model}
    (folder / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "transcript.raw.txt").write_text(video.transcript, encoding="utf-8")
    for code, text in syntheses.items():
        (folder / f"synthesis.{code}.md").write_text(text, encoding="utf-8")
    return folder


def resolve_languages(requested, source_language: str) -> dict[str, str]:
    """Ordered code -> name map: requested languages, plus the source language if missing."""
    codes = list(dict.fromkeys(c.strip().lower() for c in requested if c.strip()))
    if source_language and source_language.lower() not in codes:
        codes.append(source_language.lower())
    return {code: LANGUAGE_NAMES.get(code, code) for code in codes}


def _is_heading(line: str) -> bool:
    """A markdown '#' heading (bold lines are never terminators)."""
    return line.startswith("#")


def extract_recap(synthesis_text: str) -> str:
    """Return the first section (the '30 seconds' block) as plain text.

    The title may be a '#' heading, a bold line, or a plain line; the block ends only at the next '#' heading.
    """
    lines: list[str] = []
    for raw in synthesis_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if lines and _is_heading(line):
            break
        lines.append(line.lstrip("#").strip().replace("**", "").replace("__", ""))
    return "\n".join(lines) if len(lines) > 1 else ""


def pick_recap(syntheses: dict[str, str]) -> tuple[str, str] | None:
    """Recap of the first non-English language (configured order) with a usable recap, else English."""
    for code in [c for c in syntheses if c != "en"] + ["en"]:
        if code in syntheses:
            recap = extract_recap(syntheses[code])
            if recap:
                return code, recap
    return None


def run(url: str, output: Path, config_path: Path | None = None, log_dir: Path | None = None,
        languages_override: str | None = None) -> list[Path]:
    config = load_config(config_path)
    video = fetch_video(url)
    requested = languages_override.split(",") if languages_override else config.output_languages
    languages = resolve_languages(requested, video.language)

    syntheses = {code: synthesize(video.transcript, config.synthesis, output_language=name) for code, name in languages.items()}
    recap = pick_recap(syntheses)
    if recap:
        # Printed before export so a PDF failure does not lose it.
        print(f"\n{recap[1]}\n")
    if log_dir is not None:
        # Logged before PDF export so a PDF crash keeps the data.
        try:
            folder = save_run_log(log_dir, url, video, config.synthesis, syntheses)
            if recap:
                (folder / f"recap.{recap[0]}.md").write_text(recap[1] + "\n", encoding="utf-8")
        except OSError as exc:
            # Logging is optional: never lose the PDFs over it.
            print(f"Warning: run log not saved: {exc}", file=sys.stderr)

    outputs = []
    for code, summary in syntheses.items():
        path = output if code == "en" else output.with_stem(f"{output.stem}.{code}")
        outputs.append(export_pdf(path, title=video.title, source_url=url, generated_on=date.today(), summary=summary))
    return outputs


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        outputs = run(args.url, args.output, args.config, None if args.no_log else args.log_dir, args.lang)
    except (ConfigError, TranscriptError, SynthesisError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    for path in outputs:
        print(f"PDF written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
