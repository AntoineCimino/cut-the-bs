# Cut the BS

Cut the BS is a command-line tool that turns a YouTube link into a factual, structured PDF summary. It fetches available captions without a YouTube API key, sends the transcript to a configurable synthesis backend, and writes a report containing the video title, source link, generation date, and summary.

## Install and run

Python 3.11+ is recommended. ReportLab PDF generation requires no system packages.

```bash
cd devtools/cut-the-bs
python3 -m venv .venv
source .venv/bin/activate
make install
make run URL="https://www.youtube.com/watch?v=VIDEO_ID"
```

PDFs are written to `output/` by default (created automatically). Choose a different output path with `python3 src/main.py URL --output custom/path.pdf`. Only YouTube URLs are supported. If captions are disabled or unavailable, the command exits with a clear error.

Each run is also saved under `logs/` (change with `--log-dir`, disable with `--no-log`); logs are local, git-ignored, and may contain transcript content.

### Summary structure

Each summary starts with the "In 30 seconds" block, then a "Thesis and argument structure" section (one-sentence thesis, 3-5 main arguments with their logical links and evidence tagged as verifiable fact / speaker interpretation / unsupported claim, the implicit conclusion, and the strongest counter-argument the speaker does not address). The detail sections follow: overview, key points, facts and numbers, caveats. Edit `src/prompts/synthesis.md` to change the structure.

### Output languages

Summaries are generated for each language in `output_languages` (`config/config.yaml`, default `[en, fr]`); override per run with `--lang en,fr`. English is written to `summary.pdf`, other languages to `summary.<code>.pdf` (e.g. `summary.fr.pdf`). If the video's caption language is not in the list, it is added automatically. All versions are generated from the same transcript.

### 30-second recap

Every summary opens with an "In 30 seconds" block (max 5 short lines: what the video is, main claim, key points, "worth watching?" verdict). After export, the tool prints that block to stdout (from the first non-English summary if any, else English) and saves it as `recap.<lang>.md` in the run log folder.

## Synthesis backends

Edit `config/config.yaml`, or copy `.env.example` to `.env`. Environment variables override YAML values.

- `claude_cli` (default) runs `claude -p` non-interactively using the CLI's existing authentication. No API key is needed.
- `anthropic_api` uses the official SDK. Set `ANTHROPIC_API_KEY` and an API model identifier. This is an explicit exception to the parent monorepo's no-direct-API-key convention because this tool is intended to become a standalone public repository. API use may incur charges.
- `fcc_claude` runs `fcc-claude -p`. Install and authenticate that third-party CLI separately. If its provider needs one, `FCC_CLAUDE_API_KEY` can be set in `.env`; this tool never reads or logs it.

Backend failures, missing executables, missing credentials, and timeouts are reported explicitly. The tool does not silently switch providers, avoiding accidental transcript disclosure to another service.

## Security and privacy

**Public-repository warning:** never commit `.env`, API keys, private transcripts, generated PDFs containing sensitive material, or personal test fixtures. `.env.example` contains placeholders only. Transcripts are sent to the selected synthesis provider, so review its privacy and retention terms before processing confidential content. Transcript content is treated as untrusted data, not instructions.

## Tests

```bash
make test
```

Tests contain invented content and mocks; they make no YouTube or synthesis-provider network calls.

## Contributing

Issues and pull requests are welcome. Keep changes small and focused; never include real transcripts, API keys, or personal data in commits, issues, or test fixtures — see [Security and privacy](#security-and-privacy) above.

## License

[MIT](LICENSE)
