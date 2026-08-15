#!/usr/bin/env python3
"""Génère la documentation consolidée HTML et PDF de HDP 4.0.0."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ("Présentation générale", ROOT / "README.md"),
    ("Guide utilisateur", ROOT / "docs/USER_GUIDE_V4.0.0.md"),
    ("Installation", ROOT / "docs/INSTALLATION_V4.0.0.md"),
    ("Architecture", ROOT / "docs/ARCHITECTURE.md"),
    ("Référence API", ROOT / "docs/API_REFERENCE_V4.0.0.md"),
    ("Matrice des sources", ROOT / "docs/SOURCE_CAPABILITY_MATRIX_V4.0.0.md"),
    ("Sauvegarde et restauration", ROOT / "docs/BACKUP_RESTORE_V4.0.0.md"),
    ("Revue de sécurité", ROOT / "docs/SECURITY_REVIEW_V4.0.0.md"),
    ("Limites connues", ROOT / "docs/KNOWN_LIMITATIONS_V4.0.0.md"),
    ("Rapport de validation", ROOT / "docs/VALIDATION_REPORT_V4.0.0.md"),
    ("Historique", ROOT / "CHANGELOG.md"),
]

OUT_HTML = ROOT / "docs/Documentation_Humanitarian_Data_Platform_v4.0.0.html"
OUT_PDF = ROOT / "output/pdf/Notice_detaillee_Humanitarian_Data_Platform_v4.0.0.pdf"


def normalize_hyphens(value: str) -> str:
    """Use plain ASCII hyphens in generated publication text."""
    return value.translate({ord(char): "-" for char in "‐‑‒–—―"})


def inline_markup(value: str) -> str:
    value = html.escape(normalize_hyphens(value.strip()))
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\[([^]]+)]\(([^)]+)\)", r'<a href="\2">\1</a>', value)
    return value


def markdown_to_html(text: str) -> str:
    output: list[str] = []
    in_code = False
    in_list = False
    in_table = False
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            output.append("<p>" + inline_markup(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            flush_paragraph()
            if in_list:
                output.append("</ul>"); in_list = False
            output.append("</code></pre>" if in_code else "<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            output.append(html.escape(line) + "\n")
            continue
        if line.startswith("|") and line.endswith("|"):
            flush_paragraph()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                continue
            if not in_table:
                if in_list:
                    output.append("</ul>"); in_list = False
                output.append("<table>"); in_table = True
            output.append("<tr>" + "".join(f"<td>{inline_markup(c)}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            output.append("</table>"); in_table = False
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            if in_list:
                output.append("</ul>"); in_list = False
            level = min(len(heading.group(1)) + 1, 6)
            output.append(f"<h{level}>{inline_markup(heading.group(2))}</h{level}>")
        elif re.match(r"^[-*]\s+", line):
            flush_paragraph()
            if not in_list:
                output.append("<ul>"); in_list = True
            output.append("<li>" + inline_markup(re.sub(r"^[-*]\s+", "", line)) + "</li>")
        elif re.match(r"^\d+\.\s+", line):
            flush_paragraph()
            if not in_list:
                output.append("<ul>"); in_list = True
            output.append("<li>" + inline_markup(re.sub(r"^\d+\.\s+", "", line)) + "</li>")
        elif not line.strip():
            flush_paragraph()
            if in_list:
                output.append("</ul>"); in_list = False
        else:
            paragraph.append(line)
    flush_paragraph()
    if in_list:
        output.append("</ul>")
    if in_table:
        output.append("</table>")
    return "\n".join(output)


def build_html() -> None:
    nav = "".join(f'<li><a href="#s{i}">{html.escape(title)}</a></li>' for i, (title, _) in enumerate(DOCS, 1))
    sections = []
    for index, (title, path) in enumerate(DOCS, 1):
        sections.append(f'<section id="s{index}"><div class="section-label">PARTIE {index:02d}</div><h1>{html.escape(title)}</h1>{markdown_to_html(path.read_text(encoding="utf-8"))}</section>')
    page = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Humanitarian Data Platform 4.0.0 - Documentation</title>
<style>
:root{{--ink:#172536;--muted:#5f6f7c;--blue:#075985;--cyan:#0e7490;--pale:#e6f6f8;--line:#d5e0e5;}}
*{{box-sizing:border-box}} body{{margin:0;background:#f4f7f8;color:var(--ink);font:16px/1.62 system-ui,-apple-system,"Segoe UI",sans-serif}}
header{{background:linear-gradient(135deg,#063b52,#0e7490);color:white;padding:72px max(7vw,28px)}}
header .kicker,.section-label{{font-weight:800;letter-spacing:.14em;text-transform:uppercase;font-size:.75rem}}
header h1{{max-width:850px;font-size:clamp(2.4rem,6vw,5rem);line-height:1.02;margin:.4rem 0 1.2rem}} header p{{max-width:700px;font-size:1.15rem}}
main{{display:grid;grid-template-columns:minmax(220px,300px) minmax(0,900px);gap:36px;max-width:1280px;margin:40px auto;padding:0 28px}}
nav{{position:sticky;top:24px;align-self:start;background:white;border:1px solid var(--line);border-radius:16px;padding:22px}} nav ol{{padding-left:1.35rem;margin:0}} nav a{{color:var(--blue);text-decoration:none}}
article{{min-width:0}} section{{background:white;border:1px solid var(--line);border-radius:18px;margin-bottom:30px;padding:clamp(24px,5vw,54px);box-shadow:0 12px 28px #1730420b}}
.section-label{{color:var(--cyan)}} h1,h2,h3,h4{{line-height:1.2;color:#0c4863}} h1{{font-size:2.2rem}} h2{{margin-top:2.2rem;border-bottom:1px solid var(--line);padding-bottom:.45rem}} code,pre{{font-family:"DejaVu Sans Mono",Consolas,monospace}} code{{background:var(--pale);padding:.12rem .3rem;border-radius:4px}} pre{{background:#102b3b;color:#e9fbff;padding:18px;overflow:auto;border-radius:10px}} table{{border-collapse:collapse;width:100%;display:block;overflow:auto;margin:1.2rem 0}} td{{border:1px solid var(--line);padding:.55rem;vertical-align:top}} tr:first-child{{background:var(--pale);font-weight:700}} a{{color:var(--blue)}}
footer{{text-align:center;color:var(--muted);padding:24px 24px 60px}}
@media(max-width:850px){{main{{display:block}}nav{{position:static;margin-bottom:24px}}}} @media print{{body{{background:white}}nav{{display:none}}main{{display:block;margin:0;max-width:none}}section{{box-shadow:none;border:0;page-break-before:always}}header{{page-break-after:always}}}}
</style></head><body>
<header><div class="kicker">Documentation de référence</div><h1>Humanitarian Data Platform</h1><p>Version 4.0.0 - utilisation, installation portable, architecture, API, sources, sécurité et limites.</p><p>Édition du 15 août 2026</p></header>
<main><nav><strong>Sommaire</strong><ol>{nav}</ol></nav><article>{''.join(sections)}</article></main>
<footer>Humanitarian Data Platform 4.0.0 - documentation consolidée</footer></body></html>"""
    OUT_HTML.write_text(page, encoding="utf-8")


def pdf_text(value: str) -> str:
    value = html.escape(normalize_hyphens(value.strip()))
    value = re.sub(r"`([^`]+)`", r'<font name="DejaVuMono">\1</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"\[([^]]+)]\(([^)]+)\)", r'<font color="#075985">\1</font>', value)
    return value


def markdown_flowables(text: str, styles: dict[str, ParagraphStyle], width: float) -> list:
    story: list = []
    lines = text.splitlines()
    index = 0
    in_code = False
    code: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            story.append(Paragraph(pdf_text(" ".join(paragraph)), styles["BodyFinal"]))
            story.append(Spacer(1, 2.2 * mm))
            paragraph.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                content = "<br/>".join(html.escape(row) or "&#160;" for row in code)
                story.append(Paragraph(content, styles["CodeFinal"]))
                story.append(Spacer(1, 2 * mm)); code.clear()
            in_code = not in_code; index += 1; continue
        if in_code:
            code.append(line); index += 1; continue
        if line.startswith("|") and line.endswith("|"):
            flush_paragraph()
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [c.strip() for c in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                index += 1
            if rows:
                columns = max(len(row) for row in rows)
                rows = [row + [""] * (columns - len(row)) for row in rows]
                cell_style = styles["TableFinal"]
                data = [[Paragraph(pdf_text(cell), cell_style) for cell in row] for row in rows]
                widths = [width / columns] * columns
                table = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6F6F8")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0C4863")),
                    ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#B8CAD2")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.extend([table, Spacer(1, 3 * mm)])
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            level = min(len(heading.group(1)), 4)
            story.append(Paragraph(pdf_text(heading.group(2)), styles[f"H{level}Final"]))
        elif re.match(r"^(?:[-*]|\d+\.)\s+", line):
            flush_paragraph()
            item = re.sub(r"^(?:[-*]|\d+\.)\s+", "", line)
            story.append(Paragraph(pdf_text(item), styles["BulletFinal"], bulletText="•"))
        elif not line.strip():
            flush_paragraph()
        else:
            paragraph.append(line)
        index += 1
    flush_paragraph()
    return story


def build_pdf() -> None:
    pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuMono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
    pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold")
    base = getSampleStyleSheet()
    styles = {
        "CoverKicker": ParagraphStyle("CoverKicker", parent=base["Normal"], fontName="DejaVu-Bold", fontSize=9, leading=12, textColor=colors.HexColor("#0E7490"), alignment=TA_CENTER, spaceAfter=8),
        "CoverTitle": ParagraphStyle("CoverTitle", parent=base["Title"], fontName="DejaVu-Bold", fontSize=30, leading=34, textColor=colors.HexColor("#0C4863"), alignment=TA_CENTER, spaceAfter=12),
        "CoverSub": ParagraphStyle("CoverSub", parent=base["Normal"], fontName="DejaVu", fontSize=12, leading=18, textColor=colors.HexColor("#526772"), alignment=TA_CENTER),
        "PartFinal": ParagraphStyle("PartFinal", parent=base["Heading1"], fontName="DejaVu-Bold", fontSize=22, leading=27, textColor=colors.HexColor("#0C4863"), spaceAfter=8),
        "H1Final": ParagraphStyle("H1Final", parent=base["Heading1"], fontName="DejaVu-Bold", fontSize=16, leading=20, textColor=colors.HexColor("#0C4863"), spaceBefore=8, spaceAfter=6),
        "H2Final": ParagraphStyle("H2Final", parent=base["Heading2"], fontName="DejaVu-Bold", fontSize=13, leading=17, textColor=colors.HexColor("#075985"), spaceBefore=7, spaceAfter=5),
        "H3Final": ParagraphStyle("H3Final", parent=base["Heading3"], fontName="DejaVu-Bold", fontSize=11, leading=15, textColor=colors.HexColor("#0E7490"), spaceBefore=6, spaceAfter=4),
        "H4Final": ParagraphStyle("H4Final", parent=base["Heading4"], fontName="DejaVu-Bold", fontSize=9.5, leading=13, textColor=colors.HexColor("#172536"), spaceBefore=5, spaceAfter=3),
        "BodyFinal": ParagraphStyle("BodyFinal", parent=base["BodyText"], fontName="DejaVu", fontSize=8.4, leading=12.3, textColor=colors.HexColor("#172536"), alignment=TA_LEFT, allowWidows=0, allowOrphans=0),
        "BulletFinal": ParagraphStyle("BulletFinal", parent=base["BodyText"], fontName="DejaVu", fontSize=8.3, leading=12, leftIndent=12, firstLineIndent=-7, bulletIndent=2, spaceAfter=2),
        "CodeFinal": ParagraphStyle("CodeFinal", parent=base["Code"], fontName="DejaVuMono", fontSize=6.4, leading=8.4, textColor=colors.HexColor("#E9FBFF"), backColor=colors.HexColor("#102B3B"), borderPadding=7, leftIndent=2, rightIndent=2, splitLongWords=True),
        "TableFinal": ParagraphStyle("TableFinal", parent=base["BodyText"], fontName="DejaVu", fontSize=6.2, leading=8, textColor=colors.HexColor("#172536")),
        "TocFinal": ParagraphStyle("TocFinal", parent=base["BodyText"], fontName="DejaVu", fontSize=10, leading=15, leftIndent=10, textColor=colors.HexColor("#075985")),
    }

    def decorate(canvas, document) -> None:
        canvas.saveState()
        width, height = A4
        canvas.setFillColor(colors.HexColor("#0C4863")); canvas.rect(0, height - 8 * mm, width, 8 * mm, stroke=0, fill=1)
        canvas.setFont("DejaVu", 7); canvas.setFillColor(colors.HexColor("#607683"))
        canvas.drawString(20 * mm, 11 * mm, "Humanitarian Data Platform 4.0.0 - documentation")
        canvas.drawRightString(width - 20 * mm, 11 * mm, f"Page {document.page}")
        canvas.restoreState()

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=20 * mm, bottomMargin=18 * mm, title="Humanitarian Data Platform 4.0.0 - Documentation", author="Humanitarian Data Platform")
    story: list = [Spacer(1, 46 * mm), Paragraph("DOCUMENTATION DE RÉFÉRENCE", styles["CoverKicker"]), Paragraph("Humanitarian<br/>Data Platform", styles["CoverTitle"]), Paragraph("Version 4.0.0", styles["CoverSub"]), Spacer(1, 12 * mm), Paragraph("Utilisation · installation · architecture · API · sources · sécurité · limites", styles["CoverSub"]), Spacer(1, 26 * mm), Paragraph("Édition du 15 août 2026", styles["CoverSub"]), PageBreak(), Paragraph("Sommaire", styles["PartFinal"])]
    for index, (title, _) in enumerate(DOCS, 1):
        story.append(Paragraph(f"{index:02d}  {html.escape(title)}", styles["TocFinal"]))
    story.append(PageBreak())
    content_width = A4[0] - 40 * mm
    for index, (title, path) in enumerate(DOCS, 1):
        story.append(KeepTogether([Paragraph(f"PARTIE {index:02d}", styles["CoverKicker"]), Paragraph(html.escape(title), styles["PartFinal"]), Spacer(1, 3 * mm)]))
        story.extend(markdown_flowables(path.read_text(encoding="utf-8"), styles, content_width))
        if index < len(DOCS):
            story.append(PageBreak())
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)


def main() -> None:
    for _, path in DOCS:
        if not path.is_file():
            raise FileNotFoundError(path)
    build_html()
    build_pdf()
    print(OUT_HTML)
    print(OUT_PDF)


if __name__ == "__main__":
    main()
