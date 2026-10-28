import json
from pathlib import Path

import main
from config import AppConfig, SynthesisConfig
from transcript import Video

URL = "https://youtu.be/synthetic01"


def _patch(monkeypatch):
    monkeypatch.setattr(main, "load_config", lambda _p: AppConfig(synthesis=SynthesisConfig()))
    monkeypatch.setattr(main, "fetch_video", lambda _u: Video("Synthetic Title", "invented transcript text", "fr"))
    monkeypatch.setattr(main, "synthesize", lambda _t, _c, output_language: f"## 30 s\n**Line** in {output_language}\n## Next\nbody")
    monkeypatch.setattr(main, "export_pdf", lambda path, **_k: path)


def test_run_persists_log_and_does_not_overwrite(tmp_path: Path, monkeypatch):
    _patch(monkeypatch)
    logs = tmp_path / "logs"
    main.run(URL, tmp_path / "out.pdf", log_dir=logs)
    main.run(URL, tmp_path / "out.pdf", log_dir=logs)
    folders = sorted(logs.iterdir())
    assert len(folders) == 2 and "synthetic01" in folders[0].name
    first = folders[0]
    assert sorted(p.name for p in first.iterdir()) == ["meta.json", "recap.fr.md", "synthesis.en.md", "synthesis.fr.md", "transcript.raw.txt"]
    assert json.loads((first / "meta.json").read_text())["video_id"] == "synthetic01"
    assert (first / "synthesis.fr.md").read_text() .startswith("## 30 s")
    assert (first / "recap.fr.md").read_text() == "30 s\nLine in French\n"


def test_no_log_writes_nothing(tmp_path: Path, monkeypatch):
    _patch(monkeypatch)
    main.run(URL, tmp_path / "out.pdf", log_dir=None)
    assert not (tmp_path / "logs").exists()


def test_languages_default_override_and_source(tmp_path: Path, monkeypatch):
    _patch(monkeypatch)
    seen = []
    monkeypatch.setattr(main, "export_pdf", lambda path, **_k: seen.append(path.name) or path)
    monkeypatch.setattr(main, "fetch_video", lambda _u: Video("T", "x", "en"))
    main.run(URL, tmp_path / "summary.pdf")
    assert seen == ["summary.pdf", "summary.fr.pdf"]
    seen.clear()
    monkeypatch.setattr(main, "fetch_video", lambda _u: Video("T", "x", "de"))
    main.run(URL, tmp_path / "summary.pdf", languages_override="en")
    assert seen == ["summary.pdf", "summary.de.pdf"]


def test_recap_printed_prefers_non_english(tmp_path: Path, monkeypatch, capsys):
    _patch(monkeypatch)
    assert main.main([URL, "-o", str(tmp_path / "s.pdf"), "--no-log"]) == 0
    out = capsys.readouterr().out
    assert "Line in French" in out and "Line in English" not in out


def test_recap_falls_back_to_english_and_handles_missing_block(tmp_path: Path, monkeypatch, capsys):
    _patch(monkeypatch)
    monkeypatch.setattr(main, "fetch_video", lambda _u: Video("T", "x", "en"))
    main.main([URL, "-o", str(tmp_path / "s.pdf"), "--no-log", "--lang", "en"])
    assert "Line in English" in capsys.readouterr().out
    assert main.extract_recap("no heading here\n## X\nbody") == ""
