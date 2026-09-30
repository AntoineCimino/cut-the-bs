# CLAUDE.md — cut-the-bs

Agent instructions for the cut-the-bs project. When developed inside its parent monorepo, the monorepo's root `CLAUDE.md` rules (critical rules, orchestration, backlog format) apply on top of this file; this file is self-contained once extracted to a standalone repository.

## Commands

```bash
cd devtools/cut-the-bs && python src/main.py <video_url>
cd devtools/cut-the-bs && pytest tests/ -v
```

## Public repo — hard rules

This project is destined to be extracted as a standalone public GitHub repo.

- Never commit API keys, personal data, or sample transcripts containing personal info.
- Synthesis backend is configurable: default `claude -p` CLI (no API key); optional Anthropic API key or `fcc-claude` via config — a documented exception to the monorepo no-API-key rule for this standalone public tool.
- Mandatory manual security/PII check over the diff before any commit.

## Backlog

`tasks/backlog_cut-the-bs.md`
