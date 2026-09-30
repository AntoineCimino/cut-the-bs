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
