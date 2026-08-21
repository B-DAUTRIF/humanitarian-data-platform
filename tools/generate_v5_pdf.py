from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "HDP_V5_Documentation_et_UML.pdf"
BLUE = colors.HexColor("#075985")
CYAN = colors.HexColor("#0e7490")
INK = colors.HexColor("#163047")
PALE = colors.HexColor("#eaf6f8")
LINE = colors.HexColor("#b9d7df")


class ArchitectureDiagram(Flowable):
    def __init__(self) -> None:
        super().__init__()
        self.width, self.height = 170 * mm, 105 * mm

    def draw_box(self, x: float, y: float, w: float, h: float, title: str, fill: colors.Color) -> None:
        canvas = self.canv
        canvas.setFillColor(fill)
        canvas.setStrokeColor(LINE)
        canvas.roundRect(x, y, w, h, 4 * mm, fill=1, stroke=1)
        canvas.setFillColor(INK)
        canvas.setFont("DejaVu-Bold", 9)
        canvas.drawCentredString(x + w / 2, y + h / 2 - 3, title)

    def arrow(self, x1: float, y1: float, x2: float, y2: float) -> None:
        c = self.canv
        c.setStrokeColor(CYAN)
        c.setLineWidth(1.3)
        c.line(x1, y1, x2, y2)
        c.line(x2, y2, x2 - 4, y2 + 6)
        c.line(x2, y2, x2 + 4, y2 + 6)

    def draw(self) -> None:
        self.draw_box(55 * mm, 88 * mm, 60 * mm, 13 * mm, "Interface locale V5", PALE)
        self.draw_box(55 * mm, 64 * mm, 60 * mm, 13 * mm, "API FastAPI authentifiée", colors.white)
        self.arrow(85 * mm, 88 * mm, 85 * mm, 77 * mm)
        for x, label in ((4, "Acquisition et projets"), (59, "Intelligence HDX"), (114, "Notebooks et scripts")):
            self.draw_box(x * mm, 39 * mm, 51 * mm, 13 * mm, label, PALE)
            self.arrow(85 * mm, 64 * mm, (x + 25.5) * mm, 52 * mm)
        self.draw_box(4 * mm, 8 * mm, 51 * mm, 13 * mm, "Sources HTTPS", colors.white)
        self.draw_box(59 * mm, 8 * mm, 51 * mm, 13 * mm, "PostgreSQL / PostGIS", colors.white)
        self.draw_box(114 * mm, 8 * mm, 51 * mm, 13 * mm, "Runners sans réseau", colors.white)
        self.arrow(29.5 * mm, 39 * mm, 29.5 * mm, 21 * mm)
        self.arrow(84.5 * mm, 39 * mm, 84.5 * mm, 21 * mm)
        self.arrow(139.5 * mm, 39 * mm, 139.5 * mm, 21 * mm)


class SignalSequence(Flowable):
    def __init__(self) -> None:
        super().__init__()
        self.width, self.height = 170 * mm, 88 * mm

    def draw(self) -> None:
        c = self.canv
        labels = ["Source", "SIGNALS", "Data Grid", "Métadonnées", "Actualisation"]
        xs = [10, 46, 82, 118, 154]
        for x, label in zip(xs, labels, strict=True):
            c.setFillColor(PALE)
            c.setStrokeColor(LINE)
            c.roundRect((x - 14) * mm, 69 * mm, 28 * mm, 10 * mm, 3 * mm, fill=1, stroke=1)
            c.setFillColor(INK)
            c.setFont("DejaVu-Bold", 7.7)
            c.drawCentredString(x * mm, 73 * mm, label)
            c.setStrokeColor(colors.HexColor("#cbd5e1"))
            c.setDash(2, 2)
            c.line(x * mm, 69 * mm, x * mm, 4 * mm)
            c.setDash()
        steps = [
            (0, 1, 58, "événement + preuves"),
            (1, 1, 47, "dédoublonner + règles"),
            (1, 2, 36, "zone, thème, période"),
            (2, 3, 25, "indexer jeux et fichiers"),
            (1, 4, 14, "ressources correspondantes et échues"),
        ]
        for start, end, y, label in steps:
            x1, x2 = xs[start] * mm, xs[end] * mm
            c.setStrokeColor(CYAN)
            c.setLineWidth(1.1)
            if start == end:
                c.roundRect(x1 - 3 * mm, (y - 2) * mm, 18 * mm, 7 * mm, 2 * mm, fill=0, stroke=1)
            else:
                c.line(x1, y * mm, x2, y * mm)
                c.line(x2, y * mm, x2 - 4, y * mm + 4)
                c.line(x2, y * mm, x2 - 4, y * mm - 4)
            c.setFillColor(INK)
            c.setFont("DejaVu", 7.2)
            c.drawString(min(x1, x2) + 2 * mm, y * mm + 2.2 * mm, label)


def footer(canvas, document) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    canvas.setFont("DejaVu", 8)
    canvas.setFillColor(colors.HexColor("#60758a"))
    canvas.drawString(20 * mm, 11 * mm, "Humanitarian Data Platform V5 - documentation et UML")
    canvas.drawRightString(190 * mm, 11 * mm, f"Page {document.page}")
    canvas.restoreState()


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="H1x", parent=styles["Heading1"], fontName="DejaVu-Bold", fontSize=23, leading=28, textColor=BLUE, spaceAfter=8))
    styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontName="DejaVu-Bold", fontSize=15, leading=19, textColor=CYAN, spaceBefore=8, spaceAfter=7))
    styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontName="DejaVu", fontSize=9.5, leading=14, textColor=INK, spaceAfter=6))
    styles.add(ParagraphStyle(name="Cover", parent=styles["Title"], fontName="DejaVu-Bold", fontSize=34, leading=40, textColor=colors.white, alignment=TA_CENTER))
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title="HDP V5 - Documentation et UML", author="Humanitarian Data Platform")
    story = []
    cover = Table([[Paragraph("HUMANITARIAN DATA<br/>PLATFORM", styles["Cover"])], [Paragraph("<font color='#d7f5fb'>Version 5.0.0 - Data Grid, SIGNALS, métadonnées et notebooks</font>", ParagraphStyle(name="CoverSub", fontName="DejaVu", fontSize=12, leading=18, alignment=TA_CENTER))]], colWidths=[170 * mm], rowHeights=[70 * mm, 32 * mm])
    cover.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BLUE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOX", (0, 0), (-1, -1), 0, BLUE)]))
    story += [Spacer(1, 35 * mm), cover, Spacer(1, 18 * mm), Paragraph("Documentation générale, architecture UML, sécurité, installation et critères de validation", ParagraphStyle(name="CoverLead", fontName="DejaVu", fontSize=12, leading=18, alignment=TA_CENTER, textColor=INK)), Spacer(1, 35 * mm), Paragraph("Édition V5 - 16 août 2026", ParagraphStyle(name="Date", fontName="DejaVu", fontSize=9, alignment=TA_CENTER, textColor=CYAN)), PageBreak()]
    story += [Paragraph("1. Résultat fonctionnel", styles["H1x"]), Paragraph("HDP V5 conserve la recherche fédérée, la bibliothèque, PostGIS, SQL, les recettes, les planifications et les runners. Il ajoute une couche d'intelligence HDX sans transformer les signaux en décisions automatiques.", styles["Bodyx"])]
    raw_rows = [["Domaine", "Capacité V5", "Garantie"]] + [
        ["Data Grid", "Recherche par besoin, zone, période, format et dimension", "Officiel distingué de l'inférence HDP"],
        ["Métadonnées", "Description de chaque jeu et fichier", "Structure, dates, types, échéance, fiabilité"],
        ["SIGNALS", "Règles, recherche automatique, mise à jour échue", "Action dédupliquée et traçable"],
        ["Syndromique", "Score global, local ou thématique", "Non diagnostique, preuves conservées"],
        ["Notebooks", "nbformat 4.5, Python et R", "SHA-256 confirmé, runner sans réseau"],
    ]
    cell_style = ParagraphStyle(name="Cell", fontName="DejaVu", fontSize=7.3, leading=9.3, textColor=INK)
    head_style = ParagraphStyle(name="CellHead", parent=cell_style, fontName="DejaVu-Bold", textColor=colors.white)
    rows = [[Paragraph(value, head_style if index == 0 else cell_style) for value in row] for index, row in enumerate(raw_rows)]
    table = Table(rows, colWidths=[30 * mm, 74 * mm, 66 * mm], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BLUE), ("GRID", (0, 0), (-1, -1), .45, LINE), ("BACKGROUND", (0, 1), (-1, -1), colors.white), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [table, Spacer(1, 8 * mm), Paragraph("Principe de prudence", styles["H2x"]), Paragraph("La fiabilité est un indicateur technique de complétude, l'appartenance Data Grid inférée reste candidate, et le score syndromique ne constitue ni un diagnostic ni une alerte officielle.", styles["Bodyx"]), PageBreak()]
    story += [Paragraph("2. UML - composants", styles["H1x"]), Paragraph("Le monolithe modulaire minimise le code d'intégration. Les runners conservent une frontière distincte parce qu'ils exécutent du code utilisateur.", styles["Bodyx"]), Spacer(1, 4 * mm), ArchitectureDiagram(), Spacer(1, 3 * mm), Paragraph("Le service GitHub redondant n'est plus déployé. Les données métier restent dans PostgreSQL/PostGIS; le spool ne transporte que des jobs bornés et est purgé après persistance.", styles["Bodyx"]), PageBreak()]
    story += [Paragraph("3. UML - événements et actualisation", styles["H1x"]), Paragraph("La recherche automatique est déterministe autour du signal. Une ressource n'est programmée que si elle correspond au périmètre et si sa date attendue de mise à jour est atteinte.", styles["Bodyx"]), Spacer(1, 3 * mm), SignalSequence(), Paragraph("Chaque action conserve règle, requête, résultat, erreur et horodatages. Les contradictions et lacunes restent visibles dans la synthèse destinée à la revue humaine.", styles["Bodyx"]), PageBreak()]
    story += [Paragraph("4. Sécurité et validation", styles["H1x"])]
    bullets = [
        "API locale: token de session, cookie HttpOnly, contrôle Host/Origin/CSRF et aucune mutation par GET.",
        "SQL: analyse AST, liste positive de vues/fonctions et rôle hdp_reader non privilégié.",
        "Téléchargements: résolution publique, IP épinglée, pair vérifié et redirections revalidées.",
        "Runners: aucun réseau, UID par job, groupes de processus, limites CPU/fichiers/processus et purge.",
        "Restauration: empreinte externe, manifeste interne, chemins/liens/ratios contrôlés avant extraction.",
        "Livraison: tests Python, compilation C stricte, JavaScript analysé, build Windows CI et SHA-256.",
    ]
    for item in bullets:
        story.append(KeepTogether([Table([["✓", Paragraph(item, styles["Bodyx"])]], colWidths=[8 * mm, 158 * mm], style=TableStyle([("TEXTCOLOR", (0, 0), (0, 0), CYAN), ("FONT", (0, 0), (0, 0), "DejaVu-Bold", 12), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))]))
    story += [Spacer(1, 5 * mm), Paragraph("Installation", styles["H2x"]), Paragraph("Windows utilise l'installateur x64 avec Docker Desktop. Linux utilise install-linux.sh en mode workstation ou server; le serveur reste lié à 127.0.0.1 et s'ouvre par tunnel SSH.", styles["Bodyx"]), Paragraph("Références: data.humdata.org/dashboards/overview-of-data-grids - docs.humdata.org/about/hdx-signals - docs.humdata.org/about/hdx-signals/prompts - jupyter.org/documentation", styles["Bodyx"])]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build()
