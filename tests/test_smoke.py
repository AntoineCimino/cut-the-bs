import main


def test_entry_point_parser_accepts_url():
    assert main.build_parser().parse_args(["https://youtu.be/synthetic01"]).url == "https://youtu.be/synthetic01"


def test_recap_language_follows_configured_order_not_appended_source():
    langs = main.resolve_languages(["en", "fr"], "es")
    assert list(langs) == ["en", "fr", "es"]
    syn = {c: f"# T {c}\nline {c}\n## Next\nx" for c in langs}
    assert main.pick_recap(syn)[0] == "fr"


def test_extract_recap_keeps_bolded_verdict_line():
    text = "**En 30 secondes**\nBody\n**Worth watching? Yes.**\n\n## Suite\nx"
    assert main.extract_recap(text) == "En 30 secondes\nBody\nWorth watching? Yes."


def test_extract_recap_bold_and_plain_titles():
    assert main.extract_recap("**En 30 secondes**\nBody\n\n## Suite\nx") == "En 30 secondes\nBody"
    assert main.extract_recap("En 30 secondes\nBody\n# Suite\nx") == "En 30 secondes\nBody"


def test_pick_recap_falls_back_when_extraction_empty():
    syn = {"en": "# T\nenglish recap\n# Rest", "fr": "# only title"}
    assert main.pick_recap(syn) == ("en", "T\nenglish recap")
    assert main.pick_recap({"fr": "x"}) is None


def test_recap_printed_even_if_pdf_export_fails(monkeypatch, capsys, tmp_path):
    from types import SimpleNamespace
    cfg = SimpleNamespace(output_languages=["en"], synthesis=None)
    video = SimpleNamespace(language="en", transcript="t", title="T")
    monkeypatch.setattr(main, "load_config", lambda p: cfg)
    monkeypatch.setattr(main, "fetch_video", lambda u: video)
    monkeypatch.setattr(main, "synthesize", lambda *a, **k: "# Recap\nbody\n# Rest")
    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(main, "export_pdf", boom)
    assert main.main(["http://x", "-o", str(tmp_path / "o.pdf"), "--no-log"]) == 1
    assert "body" in capsys.readouterr().out
