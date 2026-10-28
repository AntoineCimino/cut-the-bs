from datetime import date
from pathlib import Path

from pypdf import PdfReader

from pdf_export import export_pdf


def test_pdf_contains_required_metadata_and_summary(tmp_path: Path):
    output = export_pdf(
        tmp_path / "result.pdf",
        title="Synthetic Video Title",
        source_url="https://youtu.be/synthetic-id",
        generated_on=date(2030, 1, 2),
        summary="Key point: the invented sample contains 12 units.",
    )
    text = "".join(page.extract_text() or "" for page in PdfReader(output).pages)
    assert output.read_bytes().startswith(b"%PDF")
    assert "Synthetic Video Title" in text
    assert "https://youtu.be/synthetic-id" in text
    assert "2030-01-02" in text
    assert "invented sample contains 12 units" in text


def _render_text(tmp_path: Path, summary: str) -> str:
    output = export_pdf(
        tmp_path / "r.pdf", title="T", source_url="https://youtu.be/x",
        generated_on=date(2030, 1, 2), summary=summary,
    )
    return "".join(page.extract_text() or "" for page in PdfReader(output).pages)


def test_superscripts_normalized():
    from pdf_export import _normalize_glyphs

    assert _normalize_glyphs("37ᵉ") == "37e"
    assert _normalize_glyphs("1ᵉʳ, 2ˢ, xⁿ, 1ª, 2º, 3²") == "1er, 2s, xn, 1a, 2o, 32"
    assert _normalize_glyphs("é à « » – …") == "é à « » – …"


def test_pdf_has_no_black_square_or_markdown_leaks(tmp_path: Path):
    text = _render_text(tmp_path, "\n".join([
        "## 1. Overview",
        "A 37ᵉ flight of *The Invented Guide* with **bold** text.",
        "---",
        "- item with *italic* and **bold**",
        "2 * 3 * 4 stays literal",
    ]))
    assert "■" not in text
    assert "37e flight" in text
    assert "The Invented Guide" in text
    assert "---" not in text
    assert "*The" not in text and "*italic" not in text and "**" not in text
    assert "2 * 3 * 4" in text


def test_inline_markup():
    from pdf_export import _inline

    assert _inline("*a b*") == "<i>a b</i>"
    assert _inline("**x** and *y*") == "<b>x</b> and <i>y</i>"
    assert _inline("***z***") != ""  # must not raise
    assert _inline("a < b & c") == "a &lt; b &amp; c"


def test_horizontal_rule_is_flowable():
    from reportlab.platypus import HRFlowable

    from pdf_export import _parse_summary

    flow = _parse_summary("before\n---\nafter", "T")
    assert any(isinstance(f, HRFlowable) for f in flow)
