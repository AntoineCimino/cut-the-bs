"""PDF report generation with lightweight Markdown-ish parsing.

Parses the summary produced by prompts/synthesis.md (# / ## headings,
**bold** inline spans, -/* bullets) into real ReportLab paragraph styles
instead of dumping flat escaped lines.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

# Register DejaVuSans (Unicode, accented characters) with bold/italic variants if available.
# Falls back to built-in Helvetica family if not found.
_FONT_NAME = "Helvetica"
_FONT_NAME_BOLD = "Helvetica-Bold"
_FONT_NAME_ITALIC = "Helvetica-Oblique"
_FONT_NAME_BOLD_ITALIC = "Helvetica-BoldOblique"
_FONT_DIRS = [
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/dejavu"),
    Path("C:\\Windows\\Fonts"),
]
try:
    from reportlab.pdfbase import pdfmetrics, ttfonts

    for _dir in _FONT_DIRS:
        _files = {
            "DejaVuSans": _dir / "DejaVuSans.ttf",
            "DejaVuSans-Bold": _dir / "DejaVuSans-Bold.ttf",
            "DejaVuSans-Oblique": _dir / "DejaVuSans-Oblique.ttf",
            "DejaVuSans-BoldOblique": _dir / "DejaVuSans-BoldOblique.ttf",
        }
        if not all(f.exists() for f in _files.values()):
            continue
        for _name, _file in _files.items():
            ttfonts.registerFont(ttfonts.TTFont(_name, str(_file)))
        pdfmetrics.registerFontFamily(
            "DejaVuSans", normal="DejaVuSans", bold="DejaVuSans-Bold",
            italic="DejaVuSans-Oblique", boldItalic="DejaVuSans-BoldOblique",
        )
        _FONT_NAME = "DejaVuSans"
        _FONT_NAME_BOLD = "DejaVuSans-Bold"
        _FONT_NAME_ITALIC = "DejaVuSans-Oblique"
        _FONT_NAME_BOLD_ITALIC = "DejaVuSans-BoldOblique"
        break
except Exception:
    pass  # Fall back to Helvetica if registration fails

# Sober palette: near-black body text, single dark-slate accent for headings/rules.
_INK = colors.HexColor("#1a1a1a")
_ACCENT = colors.HexColor("#2f3b52")
_MUTED = colors.HexColor("#5a5a5a")
_RULE = colors.HexColor("#c7ccd6")

_H1 = ParagraphStyle("H1", fontName=_FONT_NAME_BOLD, fontSize=13, leading=16,
                      textColor=_ACCENT, spaceBefore=10 * mm, spaceAfter=3 * mm)
_H2 = ParagraphStyle("H2", fontName=_FONT_NAME_BOLD, fontSize=10.5, leading=13,
                      textColor=_ACCENT, spaceBefore=4 * mm, spaceAfter=2 * mm)
_BODY = ParagraphStyle("Body", fontName=_FONT_NAME, fontSize=9.5, leading=14,
                        textColor=_INK, alignment=TA_LEFT, spaceAfter=2 * mm)
_BULLET = ParagraphStyle("Bullet", parent=_BODY, spaceAfter=1 * mm)
_COVER_TITLE = ParagraphStyle("CoverTitle", fontName=_FONT_NAME_BOLD, fontSize=18,
                               leading=22, textColor=_INK, spaceAfter=3 * mm)
_COVER_META = ParagraphStyle("CoverMeta", fontName=_FONT_NAME, fontSize=8.5,
                              leading=12, textColor=_MUTED)


def _normalize_glyphs(text: str) -> str:
    """Replace superscript/subscript/modifier letters with plain equivalents.

    Characters such as "ᵉ" (U+1D49), "ˢ", "ⁿ", "ª", "º" are missing from the PDF
    font and render as a black square. Their compatibility decomposition
    (e.g. "37ᵉ" -> "37e") is safe and readable.
    """
    out = []
    for ch in text:
        if ord(ch) > 0x7F and re.match(r"<(super|sub)>", unicodedata.decomposition(ch)):
            out.append(unicodedata.normalize("NFKC", ch))
        else:
            out.append(ch)
    return "".join(out)


_HR_RE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")


def _inline(text: str) -> str:
    """Escape, then translate **bold** and *italic* spans to ReportLab tags."""
    escaped = escape(_normalize_glyphs(text))
    bolded = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    return re.sub(r"(?<![*\w])\*(?![\s*])(.+?)(?<![\s*])\*(?![*\w])", r"<i>\1</i>", bolded)


def _parse_summary(summary: str, cover_title: str) -> list[Flowable]:
    flowables: list[Flowable] = []
    bullet_buffer: list[str] = []

    def flush_bullets() -> None:
        if bullet_buffer:
            items = [ListItem(Paragraph(_inline(b), _BULLET), leftIndent=0) for b in bullet_buffer]
            flowables.append(ListFlowable(items, bulletType="bullet", start="-",
                                           leftIndent=5 * mm, bulletFontSize=9,
                                           bulletColor=_MUTED, spaceAfter=2 * mm))
            bullet_buffer.clear()

    for raw_line in summary.split("\n"):
        line = raw_line.strip()
        if not line:
            flush_bullets()
            continue
        if _HR_RE.match(line):
            flush_bullets()
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=_RULE,
                                         spaceBefore=2 * mm, spaceAfter=3 * mm))
        elif line.startswith("## "):
            flush_bullets()
            flowables.append(Paragraph(_inline(line[3:].strip()), _H1))
        elif line.startswith("# "):
            heading = line[2:].strip()
            # ponytail: skip a leading H1 that duplicates the cover title (LLM often repeats it).
            if heading != cover_title:
                flush_bullets()
                flowables.append(Paragraph(_inline(heading), _H1))
        elif line.startswith(("- ", "* ")):
            bullet_buffer.append(line[2:].strip())
        elif line.startswith("**") and line.endswith("**") and line.count("**") == 2:
            flush_bullets()
            flowables.append(Paragraph(_inline(line), _H2))
        else:
            flush_bullets()
            flowables.append(Paragraph(_inline(line), _BODY))
    flush_bullets()
    return flowables


def export_pdf(output: Path, *, title: str, source_url: str, generated_on: date, summary: str) -> Path:
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    story: list[Flowable] = [
        Paragraph(escape(_normalize_glyphs(title)), _COVER_TITLE),
        Paragraph(f"Source: {escape(source_url)}", _COVER_META),
        Paragraph(f"Generated: {generated_on.isoformat()}", _COVER_META),
        Spacer(1, 3 * mm),
        HRFlowable(width="100%", thickness=0.75, color=_RULE, spaceAfter=4 * mm),
    ]
    story.extend(_parse_summary(summary, title))

    SimpleDocTemplate(
        str(output), pagesize=A4,
        rightMargin=20 * mm, leftMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
    ).build(story)
    return output
