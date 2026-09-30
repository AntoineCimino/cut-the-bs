import json
from pathlib import Path

import main
from config import AppConfig, SynthesisConfig
from transcript import Video

URL = "https://youtu.be/synthetic01"


def _patch(monkeypatch):
    monkeypatch.setattr(main, "load_config", lambda _p: AppConfig(synthesis=SynthesisConfig()))
    monkeypatch.setattr(main, "fetch_video", lambda _u: Video("Synthetic Title", "invented transcript text", "fr"))
    monkeypatch.setattr(main, "synthesize", lambda _t, _c, output_language: f"summary in {output_language}")
    monkeypatch.setattr(main, "export_pdf", lambda path, **_k: path)


def test_run_persists_log_and_does_not_overwrite(tmp_path: Path, monkeypatch):
    _patch(monkeypatch)
    logs = tmp_path / "logs"
    main.run(URL, tmp_path / "out.pdf", log_dir=logs)
    main.run(URL, tmp_path / "out.pdf", log_dir=logs)
    folders = sorted(logs.iterdir())
    assert len(folders) == 2 and "synthetic01" in folders[0].name
    first = folders[0]
    assert sorted(p.name for p in first.iterdir()) == ["meta.json", "synthesis.en.md", "synthesis.fr.md", "transcript.raw.txt"]
    assert json.loads((first / "meta.json").read_text())["video_id"] == "synthetic01"
    assert (first / "synthesis.fr.md").read_text() == "summary in French"


def test_no_log_writes_nothing(tmp_path: Path, monkeypatch):
    _patch(monkeypatch)
    main.run(URL, tmp_path / "out.pdf", log_dir=None)
    assert not (tmp_path / "logs").exists()
