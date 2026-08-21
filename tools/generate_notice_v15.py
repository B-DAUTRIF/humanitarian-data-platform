from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "Notice_detaillee_Humanitarian_Data_Platform_v1.5.pdf"

NAVY = colors.HexColor("#0B1F33")
BLUE = colors.HexColor("#1479B8")
CYAN = colors.HexColor("#3CB7D6")
GREEN = colors.HexColor("#16856A")
ORANGE = colors.HexColor("#D67A22")
RED = colors.HexColor("#B13A45")
INK = colors.HexColor("#172433")
MUTED = colors.HexColor("#5E6B78")
LINE = colors.HexColor("#D7E0E8")
PALE_BLUE = colors.HexColor("#EAF5FB")
PALE_GREEN = colors.HexColor("#E9F6F1")
PALE_ORANGE = colors.HexColor("#FFF4E6")
PALE_RED = colors.HexColor("#FCEDEF")
PALE_GREY = colors.HexColor("#F4F6F8")
WHITE = colors.white


def register_fonts() -> None:
    font_dir = Path("/usr/share/fonts/truetype/dejavu")
    pdfmetrics.registerFont(TTFont("HDP", str(font_dir / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("HDP-Bold", str(font_dir / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("HDP-Mono", str(font_dir / "DejaVuSansMono.ttf")))


register_fonts()


BASE = getSampleStyleSheet()
STYLES = {
    "title": ParagraphStyle(
        "TitleHDP", parent=BASE["Title"], fontName="HDP-Bold", fontSize=27,
        leading=32, textColor=WHITE, alignment=TA_LEFT, spaceAfter=8,
    ),
    "subtitle": ParagraphStyle(
        "SubtitleHDP", parent=BASE["Normal"], fontName="HDP", fontSize=13,
        leading=18, textColor=colors.HexColor("#CFE8F5"), spaceAfter=8,
    ),
    "h1": ParagraphStyle(
        "Heading1HDP", parent=BASE["Heading1"], fontName="HDP-Bold", fontSize=18,
        leading=23, textColor=NAVY, spaceBefore=3, spaceAfter=10, keepWithNext=True,
    ),
    "h2": ParagraphStyle(
        "Heading2HDP", parent=BASE["Heading2"], fontName="HDP-Bold", fontSize=12,
        leading=16, textColor=BLUE, spaceBefore=9, spaceAfter=6, keepWithNext=True,
    ),
    "body": ParagraphStyle(
        "BodyHDP", parent=BASE["BodyText"], fontName="HDP", fontSize=9.4,
        leading=13.4, textColor=INK, alignment=TA_LEFT, spaceAfter=6,
    ),
    "small": ParagraphStyle(
        "SmallHDP", parent=BASE["BodyText"], fontName="HDP", fontSize=7.8,
        leading=10.8, textColor=MUTED, spaceAfter=4,
    ),
    "table": ParagraphStyle(
        "TableHDP", parent=BASE["BodyText"], fontName="HDP", fontSize=7.6,
        leading=10.2, textColor=INK,
    ),
    "table_bold": ParagraphStyle(
        "TableBoldHDP", parent=BASE["BodyText"], fontName="HDP-Bold", fontSize=7.6,
        leading=10.2, textColor=INK,
    ),
    "table_header": ParagraphStyle(
        "TableHeaderHDP", parent=BASE["BodyText"], fontName="HDP-Bold", fontSize=7.6,
        leading=10.2, textColor=WHITE,
    ),
    "code": ParagraphStyle(
        "CodeHDP", parent=BASE["Code"], fontName="HDP-Mono", fontSize=7.5,
        leading=10.2, textColor=INK, leftIndent=0, rightIndent=0,
    ),
    "toc1": ParagraphStyle(
        "TOC1", parent=BASE["Normal"], fontName="HDP-Bold", fontSize=9.4,
        leading=13, leftIndent=0, firstLineIndent=0, textColor=NAVY,
    ),
    "toc2": ParagraphStyle(
        "TOC2", parent=BASE["Normal"], fontName="HDP", fontSize=8.5,
        leading=11.5, leftIndent=14, firstLineIndent=0, textColor=MUTED,
    ),
    "center": ParagraphStyle(
        "CenterHDP", parent=BASE["BodyText"], fontName="HDP", fontSize=9,
        leading=13, alignment=TA_CENTER, textColor=MUTED,
    ),
}


class ArchitectureDiagram(Flowable):
    def __init__(self) -> None:
        super().__init__()
        self.width = 174 * mm
        self.height = 78 * mm

    def draw_box(self, x: float, y: float, w: float, h: float, title: str, detail: str, fill) -> None:
        c = self.canv
        c.setFillColor(fill)
        c.setStrokeColor(LINE)
        c.roundRect(x, y, w, h, 6, fill=1, stroke=1)
        c.setFillColor(NAVY)
        c.setFont("HDP-Bold", 8)
        c.drawString(x + 7, y + h - 13, title)
        c.setFillColor(MUTED)
        c.setFont("HDP", 6.6)
        c.drawString(x + 7, y + 8, detail)

    def arrow(self, x1: float, y1: float, x2: float, y2: float) -> None:
        c = self.canv
        c.setStrokeColor(BLUE)
        c.setFillColor(BLUE)
        c.setLineWidth(1.2)
        c.line(x1, y1, x2, y2)
        if abs(x2 - x1) >= abs(y2 - y1):
            direction = 1 if x2 >= x1 else -1
            c.line(x2, y2, x2 - 5 * direction, y2 + 3)
            c.line(x2, y2, x2 - 5 * direction, y2 - 3)
        else:
            direction = 1 if y2 >= y1 else -1
            c.line(x2, y2, x2 + 3, y2 - 5 * direction)
            c.line(x2, y2, x2 - 3, y2 - 5 * direction)

    def draw(self) -> None:
        self.draw_box(5, 155, 130, 43, "Navigateur Windows", "Interface locale", PALE_BLUE)
        self.draw_box(186, 155, 130, 43, "API FastAPI", "Python 3.12 - port interne 8080", PALE_GREEN)
        self.draw_box(367, 155, 120, 43, "Sources publiques", "ReliefWeb et HDX/CKAN", PALE_ORANGE)
        self.draw_box(5, 60, 130, 43, "Fichiers JSON", "data/raw + SHA-256", PALE_GREY)
        self.draw_box(186, 60, 130, 43, "PostgreSQL/PostGIS", "Volume Docker persistant", PALE_BLUE)
        self.draw_box(367, 60, 120, 43, "R/plumber", "Profil analytics optionnel", PALE_GREEN)
        self.arrow(135, 176, 186, 176)
        self.arrow(316, 176, 367, 176)
        self.arrow(226, 155, 226, 103)
        self.arrow(276, 155, 407, 103)
        self.arrow(186, 166, 135, 82)
        c = self.canv
        c.setFont("HDP", 6.6)
        c.setFillColor(MUTED)
        c.drawCentredString(160, 184, "HTTP 127.0.0.1")
        c.drawCentredString(341, 184, "HTTPS sortant")
        c.drawCentredString(251, 128, "SQL")


class HDPDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str) -> None:
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=20 * mm,
            bottomMargin=18 * mm,
            title="Notice détaillée - Humanitarian Data Platform v1.5",
            author="Humanitarian Data Platform",
            subject="Installation, utilisation, architecture, données, sécurité et diagnostic",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="body",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=self.draw_page))
        self.heading_counter = 0

    def beforeDocument(self) -> None:
        self.heading_counter = 0

    def draw_page(self, canvas, doc) -> None:
        canvas.saveState()
        page = doc.page
        if page > 1:
            canvas.setStrokeColor(LINE)
            canvas.setLineWidth(0.6)
            canvas.line(18 * mm, A4[1] - 13 * mm, A4[0] - 18 * mm, A4[1] - 13 * mm)
            canvas.setFont("HDP", 7.2)
            canvas.setFillColor(MUTED)
            canvas.drawString(18 * mm, A4[1] - 10 * mm, "HUMANITARIAN DATA PLATFORM - NOTICE v1.5")
            canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {page}")
            canvas.setStrokeColor(LINE)
            canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
        canvas.restoreState()

    def afterFlowable(self, flowable) -> None:
        if not isinstance(flowable, Paragraph):
            return
        style = flowable.style.name
        if style not in ("Heading1HDP", "Heading2HDP"):
            return
        level = 0 if style == "Heading1HDP" else 1
        text = flowable.getPlainText()
        self.heading_counter += 1
        key = f"heading-{self.heading_counter}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page, key))


def P(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, STYLES[style])


def H1(text: str) -> Paragraph:
    return P(text, "h1")


def H2(text: str) -> Paragraph:
    return P(text, "h2")


def bullets(items: list[str], level: int = 0) -> ListFlowable:
    return ListFlowable(
        [ListItem(P(item), leftIndent=0) for item in items],
        bulletType="bullet",
        bulletChar="-",
        leftIndent=(13 + level * 10),
        bulletFontName="HDP-Bold",
        bulletFontSize=8,
        spaceAfter=6,
    )


def callout(title: str, text: str, kind: str = "info") -> Table:
    palette = {
        "info": (PALE_BLUE, BLUE),
        "success": (PALE_GREEN, GREEN),
        "warning": (PALE_ORANGE, ORANGE),
        "danger": (PALE_RED, RED),
    }
    background, border = palette[kind]
    body = P(f"<b>{title}</b><br/>{text}")
    table = Table([[body]], colWidths=[174 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.8, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def codebox(lines: str) -> Table:
    escaped = lines.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    body = P(escaped.replace("\n", "<br/>"), "code")
    table = Table([[body]], colWidths=[174 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE_GREY),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def data_table(rows: list[list[str]], widths: list[float], header: bool = True) -> Table:
    converted = []
    for row_index, row in enumerate(rows):
        style = "table_header" if header and row_index == 0 else "table"
        converted.append([P(cell, style) for cell in row])
    table = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE_GREY]),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ]
    table.setStyle(TableStyle(commands))
    return table


def add_page_title(story: list, title: str, intro: str | None = None) -> None:
    story.append(H1(title))
    if intro:
        story.append(P(intro))


def build_story() -> list:
    s: list = []

    # Couverture
    cover = Table(
        [[P("HUMANITARIAN DATA PLATFORM", "subtitle")],
         [P("Notice détaillée<br/>d'installation et d'utilisation", "title")],
         [P("Version 1.5.0 - Windows 10/11 x64 - Application locale", "subtitle")]],
        colWidths=[174 * mm],
        rowHeights=[16 * mm, 47 * mm, 20 * mm],
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    s += [Spacer(1, 20 * mm), cover, Spacer(1, 13 * mm)]
    s.append(callout(
        "Etat validé le 7 août 2026",
        "Installation réussie sur Windows 11 : API FastAPI et PostgreSQL/PostGIS sains, interface en HTTP 200 sur <b>http://localhost:18080</b>. Le port 8080 étant occupé, la sélection automatique de port de la v1.5 a fonctionné.",
        "success",
    ))
    s += [Spacer(1, 10 * mm)]
    s.append(data_table([
        ["Document", "Valeur"],
        ["Objet", "Installation, usage, architecture, données, sécurité, diagnostic et maintenance"],
        ["Public", "Utilisateur Windows, analyste de données, développeur ou mainteneur"],
        ["Portée", "MVP local de développement, non durci pour Internet ou le multi-utilisateur"],
        ["Fichier principal", "HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe"],
    ], [42 * mm, 132 * mm]))
    s += [Spacer(1, 10 * mm), P("Document généré à partir du code source v1.5 et du diagnostic Windows réussi. Les limites réelles de la version sont indiquées explicitement.", "center"), PageBreak()]

    # Sommaire
    s.append(H1("Sommaire"))
    toc = TableOfContents()
    toc.levelStyles = [STYLES["toc1"], STYLES["toc2"]]
    toc.dotsMinLevel = 0
    s += [toc, PageBreak()]

    # 1
    add_page_title(s, "1. Finalité, portée et état de la version 1.5")
    s.append(P(
        "Humanitarian Data Platform (HDP) est un socle local client-serveur destiné à centraliser progressivement l'accès aux données humanitaires publiques. La v1.5 fournit une interface de recherche dans le navigateur, une API Python, un archivage traçable des réponses et une base géospatiale prête à être enrichie."
    ))
    s.append(H2("1.1 Fonctions opérationnelles"))
    s.append(bullets([
        "Recherche de rapports ReliefWeb via l'API v2, sous réserve d'un appname pré-approuvé.",
        "Recherche de jeux de données HDX via l'action CKAN package_search.",
        "Affichage des titres, dates, sources et liens des résultats.",
        "Archivage du JSON de réponse dans data/raw, avec date UTC, requête assainie et UUID.",
        "Calcul d'une empreinte SHA-256 et enregistrement de la provenance dans PostgreSQL.",
        "Accès à l'historique des acquisitions par l'API.",
        "Service R/plumber optionnel pour un résumé descriptif simple.",
        "Installation graphique Windows, diagnostic et gestion automatique du port local.",
    ]))
    s.append(H2("1.2 Ce que la v1.5 ne fait pas encore"))
    s.append(bullets([
        "Elle ne télécharge pas les fichiers de ressources associés aux jeux de données HDX.",
        "Elle ne planifie pas les acquisitions et ne possède pas de file de tâches.",
        "Elle ne normalise pas encore les données selon un modèle humanitaire commun.",
        "PostGIS est activé, mais aucune table géométrique ou carte n'est encore exploitée.",
        "L'interface ne présente ni historique des acquisitions ni analyse R complète.",
        "Il n'existe ni authentification, ni TLS local, ni mode serveur multi-utilisateur.",
    ]))
    s.append(callout("Positionnement", "La v1.5 est un MVP local de développement validé sur une machine Windows. Ce n'est pas un produit de production ni un serveur exposable directement sur Internet.", "warning"))
    s.append(PageBreak())

    # 2
    add_page_title(s, "2. Architecture technique")
    s.append(ArchitectureDiagram())
    s.append(Spacer(1, 4 * mm))
    s.append(P(
        "L'utilisateur ouvre l'interface depuis Windows. Docker publie uniquement le port de l'API sur 127.0.0.1. FastAPI interroge les sources distantes en HTTPS, écrit les fichiers JSON dans un dossier monté depuis Windows et enregistre la provenance dans PostgreSQL/PostGIS. Le service R reste interne au réseau Compose."
    ))
    s.append(H2("2.1 Composants et versions embarquées"))
    s.append(data_table([
        ["Composant", "Implémentation v1.5", "Rôle"],
        ["Installateur", "C/Win32, PE32+ GUI x86-64", "Analyse, dépendances, déploiement, logs et navigateur"],
        ["API", "Python 3.12, FastAPI 0.116.1, Uvicorn 0.35.0", "Routes, validation, connecteurs et provenance"],
        ["Client HTTP", "httpx 0.28.1", "Appels ReliefWeb et HDX"],
        ["Base", "PostgreSQL 16 + PostGIS 3.4", "Métadonnées d'acquisition et extension géospatiale"],
        ["Accès SQL", "psycopg 3.2.9", "Initialisation et requêtes PostgreSQL"],
        ["Analyses", "R 4.4.3 + plumber/jsonlite", "Service analytique optionnel"],
        ["Orchestration", "Docker Compose", "Réseau, volumes, santé et profil analytics"],
    ], [34 * mm, 61 * mm, 79 * mm]))
    s.append(H2("2.2 Isolation réseau"))
    s.append(bullets([
        "L'API écoute dans son conteneur sur 0.0.0.0:8080, mais le port hôte est lié à 127.0.0.1 uniquement.",
        "PostgreSQL n'a aucune section ports dans Compose : il n'est accessible que sur le réseau Docker.",
        "R utilise expose: 8001 sans publication Windows.",
        "Les conteneurs communiquent par leurs noms de service db et r-service.",
    ]))
    s.append(PageBreak())

    # 3
    add_page_title(s, "3. Prérequis Windows")
    s.append(H2("3.1 Configuration minimale raisonnable"))
    s.append(data_table([
        ["Elément", "Exigence ou recommandation"],
        ["Système", "Windows 10/11 x64 pris en charge par Docker Desktop ; Windows 11 conseillé"],
        ["Virtualisation", "Virtualisation matérielle activée dans le BIOS/UEFI"],
        ["WSL", "WSL 2 ; Docker indique actuellement WSL 2.1.5 au minimum"],
        ["Mémoire", "8 Go de RAM minimum selon Docker Desktop ; davantage conseillé pour R et les données"],
        ["Disque", "10 Go libres recommandés avant les constructions et acquisitions importantes"],
        ["Réseau", "Connexion Internet pour les images Docker, les paquets et les API distantes"],
        ["Navigateur", "Navigateur Windows moderne"],
        ["winget", "Présent sur Windows moderne via App Installer ; utilisé pour les tiers sélectionnés"],
    ], [45 * mm, 129 * mm]))
    s.append(callout(
        "Espace disque",
        "L'installateur avertit sous 5 Gio libres sur le disque de LOCALAPPDATA et recommande 10 Go. Le diagnostic réussi indiquait 13,8 Gio libres sur C:. Docker stocke par défaut ses données WSL sous AppData\\Local\\Docker\\wsl, sauf déplacement dans ses paramètres.",
        "warning",
    ))
    s.append(H2("3.2 Logiciels tiers"))
    s.append(P(
        "Docker Desktop est requis. Git et Visual Studio Code sont proposés pour le développement mais ne sont pas nécessaires à l'exécution quotidienne. Aucune case n'est cochée automatiquement. L'utilisateur choisit les installations autorisées, puis confirme. Les conditions initiales de Docker Desktop doivent être lues et acceptées dans Docker par l'utilisateur lui-même."
    ))
    s.append(P(
        "Les conditions de licence de Docker Desktop dépendent du contexte d'usage et peuvent évoluer. La notice ne remplace pas les conditions publiées par Docker."
    ))
    s.append(PageBreak())

    # 4
    add_page_title(s, "4. Contenu des livrables v1.5")
    s.append(data_table([
        ["Fichier", "Utilité"],
        ["HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe", "Installateur Windows natif principal"],
        ["...v1.5.exe.sha256", "Empreinte attendue de l'exécutable"],
        ["HumanitarianDataPlatform_Windows_v1.5.zip", "Paquet Windows : EXE, empreinte, notice courte et diagnostic"],
        ["HumanitarianDataPlatform_Source_v1.5.zip", "Sources de l'installateur et du payload, script de build et test"],
        ["HumanitarianDataPlatform_Setup_README_v1.5.txt", "Notice courte de version"],
        ["HDP_Diagnostic_v1.5.cmd", "Diagnostic borné produisant un journal sur le Bureau"],
        ["Notice_detaillee_Humanitarian_Data_Platform_v1.5.pdf", "Le présent document"],
        ["HDP_Prompt_exhaustif_reprise_GPT_Plus_v1.5.txt", "Prompt autonome pour une nouvelle instance GPT+"],
    ], [80 * mm, 94 * mm]))
    s.append(H2("4.1 Empreinte de l'exécutable"))
    s.append(codebox("SHA-256 attendu :\n1e77042dbbd7a7d400c690076bc61e3c7191c5e928cdb016a39292af2a362470"))
    s.append(P("Vérification dans PowerShell depuis le dossier de téléchargement :"))
    s.append(codebox("Get-FileHash .\\HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe -Algorithm SHA256"))
    s.append(callout(
        "Signature Windows",
        "L'exécutable n'est pas signé par un certificat d'éditeur. Windows SmartScreen peut donc afficher un avertissement. Vérifier l'empreinte avant l'exécution et ne pas contourner une alerte si le fichier ou son origine diffère.",
        "warning",
    ))
    s.append(PageBreak())

    # 5
    add_page_title(s, "5. Installation pas à pas")
    s.append(H2("5.1 Préparation"))
    s.append(bullets([
        "Décompresser HumanitarianDataPlatform_Windows_v1.5.zip dans un dossier local.",
        "Vérifier l'empreinte SHA-256 de l'exécutable.",
        "Fermer les opérations Docker en cours et vérifier l'espace libre.",
        "Si Docker Desktop est déjà installé, l'ouvrir avant de lancer HDP réduit le temps d'attente.",
    ]))
    s.append(H2("5.2 Ecran de l'installateur"))
    s.append(bullets([
        "Dossier d'installation : conserver de préférence %USERPROFILE%\\HumanitarianDataPlatform.",
        "Appname ReliefWeb : laisser vide pour utiliser uniquement HDX, ou saisir l'identifiant pré-approuvé.",
        "Docker Desktop : cocher uniquement s'il est absent et si son installation est autorisée.",
        "Git et Visual Studio Code : optionnels.",
        "Module analytique R : facultatif et différable.",
        "Cliquer sur Analyser à nouveau pour rafraîchir l'état des dépendances.",
        "Cliquer sur Installer et ouvrir, puis confirmer le périmètre choisi.",
    ]))
    s.append(H2("5.3 Déroulement automatique"))
    s.append(data_table([
        ["Etape", "Action"],
        ["1", "Installation winget des tiers explicitement sélectionnés"],
        ["2", "Ecriture du payload FastAPI, PostgreSQL/PostGIS et R/plumber"],
        ["3", "Choix et persistance d'un port local disponible"],
        ["4", "Création ou mise à jour de .env en préservant le secret existant"],
        ["5", "Vérification du moteur Docker ; ouverture de Docker si nécessaire"],
        ["6", "Téléchargement de l'image PostGIS et construction de l'API"],
        ["7", "Construction éventuelle du service R"],
        ["8", "Démarrage Compose et attente des healthchecks"],
        ["9", "Validation /api/health puis ouverture du navigateur"],
    ], [18 * mm, 156 * mm]))
    s.append(callout(
        "Premier démarrage de Docker",
        "Si Docker affiche ses conditions ou demande une mise à jour WSL, terminer cette étape dans la fenêtre Docker. HDP attend le moteur pendant au plus six minutes et poursuit automatiquement lorsqu'il répond.",
        "info",
    ))
    s.append(PageBreak())

    # 6
    add_page_title(s, "6. Gestion automatique du port local")
    s.append(P(
        "Le port interne de FastAPI reste 8080. Seul le port Windows change. L'installateur lie toujours l'adresse à 127.0.0.1 pour éviter une exposition involontaire sur le réseau local."
    ))
    s.append(H2("6.1 Algorithme de sélection"))
    s.append(bullets([
        "Lire HDP_PORT dans la configuration existante.",
        "Conserver ce port si HDP y répond ou si un bind exclusif Winsock est possible.",
        "Sinon essayer 8080.",
        "Sinon parcourir 18080 à 18279 et choisir le premier port libre.",
        "Ecrire le port dans .env et l'utiliser dans Compose, la sonde, le navigateur et les scripts de démarrage.",
    ]))
    s.append(H2("6.2 Retrouver l'adresse"))
    s.append(P("Ouvrir le fichier suivant sans divulguer les autres variables :"))
    s.append(codebox("%USERPROFILE%\\HumanitarianDataPlatform\\.env\n\nHDP_PORT=18080"))
    s.append(P("L'adresse devient alors :"))
    s.append(codebox("http://localhost:18080"))
    s.append(callout("Validation v1.5", "Sur la machine de test, 0.0.0.0:8080 était occupé par un autre processus. HDP a choisi 18080, recréé l'API et terminé l'installation avec succès.", "success"))
    s.append(PageBreak())

    # 7
    add_page_title(s, "7. Première utilisation dans le navigateur")
    s.append(H2("7.1 Recherche HDX/CKAN"))
    s.append(bullets([
        "Choisir HDX / CKAN.",
        "Saisir au moins deux caractères, par exemple choléra Mozambique.",
        "Choisir de 1 à 100 résultats.",
        "Cliquer sur Rechercher et archiver.",
        "Ouvrir un résultat dans un nouvel onglet pour consulter sa fiche HDX.",
    ]))
    s.append(P(
        "La v1.5 appelle package_search et présente les métadonnées des jeux de données. Elle ne télécharge pas les fichiers ou ressources CKAN référencés par ces jeux."
    ))
    s.append(H2("7.2 Recherche ReliefWeb"))
    s.append(P(
        "ReliefWeb exige un appname pré-approuvé depuis le 1er novembre 2025. Sans cette valeur, l'API HDP retourne une erreur 503 explicite ; HDX reste utilisable. La v1.5 interroge uniquement le type reports."
    ))
    s.append(bullets([
        "Obtenir un appname selon la procédure officielle ReliefWeb.",
        "Le saisir lors d'une relance de l'installateur, ou modifier RELIEFWEB_APPNAME dans .env.",
        "Après une modification manuelle de .env, redémarrer les services avec stop-hdp.cmd puis start-hdp.cmd.",
        "Respecter les droits des producteurs, les quotas et les conditions d'utilisation des contenus.",
    ]))
    s.append(H2("7.3 Lire le résultat d'acquisition"))
    s.append(data_table([
        ["Champ affiché", "Interprétation"],
        ["Acquisition", "UUID unique généré localement"],
        ["Nombre d'éléments", "Nombre de résultats simplifiés retournés par HDP"],
        ["SHA-256", "Empreinte du JSON re-sérialisé et archivé"],
        ["Lien du résultat", "Page ReliefWeb ou HDX déterminée par la source"],
    ], [52 * mm, 122 * mm]))
    s.append(PageBreak())

    # 8
    add_page_title(s, "8. API locale")
    s.append(P("FastAPI expose une documentation interactive à l'adresse /docs. Les routes suivantes existent dans la v1.5 :"))
    s.append(data_table([
        ["Méthode et route", "Rôle", "Paramètres / résultat"],
        ["GET /", "Interface HTML", "Formulaire de recherche"],
        ["GET /api/health", "Santé API + SQL", "status, application, version"],
        ["GET /api/sources", "Sources déclarées", "ReliefWeb et HDX/CKAN"],
        ["GET /api/search", "Recherche + archivage", "source, query, limit"],
        ["GET /api/acquisitions", "Historique JSON", "limit de 1 à 200"],
        ["GET /api/analysis/status", "Etat de R", "ok ou not_started"],
        ["GET /docs", "Swagger UI", "Documentation générée"],
        ["GET /openapi.json", "Schéma OpenAPI", "Description machine"],
    ], [51 * mm, 49 * mm, 74 * mm]))
    s.append(H2("8.1 Exemples"))
    s.append(codebox("http://localhost:18080/api/health\nhttp://localhost:18080/api/acquisitions?limit=20\nhttp://localhost:18080/api/search?source=hdx&query=cholera&limit=10"))
    s.append(callout(
        "Attention",
        "Une URL /api/search déclenche une acquisition et écrit un fichier ainsi qu'une ligne PostgreSQL. Ne pas l'utiliser comme simple test répétitif si l'on souhaite éviter des archives en double.",
        "warning",
    ))
    s.append(PageBreak())

    # 9
    add_page_title(s, "9. Données, provenance et intégrité")
    s.append(H2("9.1 Fichiers bruts"))
    s.append(P("Structure générale :"))
    s.append(codebox("data\\raw\\<source>\\YYYYMMDDTHHMMSSZ_<requete>_<uuid>.json"))
    s.append(P(
        "Le JSON reçu est d'abord décodé en objet Python, puis re-sérialisé en UTF-8 avec tri des clés. Le fichier préserve le contenu structuré retourné, mais pas nécessairement l'ordre des clés, les espaces ni les octets exacts de la réponse HTTP originale. L'empreinte SHA-256 porte sur cette version archivée."
    ))
    s.append(H2("9.2 Métadonnées PostgreSQL"))
    s.append(data_table([
        ["Colonne", "Type", "Sens"],
        ["id", "UUID", "Identifiant primaire de l'acquisition"],
        ["source", "TEXT", "reliefweb ou hdx"],
        ["query", "TEXT", "Requête saisie"],
        ["retrieved_at", "TIMESTAMPTZ", "Date UTC d'acquisition"],
        ["sha256", "CHAR(64)", "Empreinte du fichier archivé"],
        ["item_count", "INTEGER", "Nombre d'éléments simplifiés"],
        ["raw_path", "TEXT", "Chemin relatif sous data"],
    ], [38 * mm, 34 * mm, 102 * mm]))
    s.append(H2("9.3 Interprétation correcte de SHA-256"))
    s.append(bullets([
        "L'empreinte permet de détecter une modification ultérieure du fichier archivé.",
        "Elle ne prouve pas que la source distante était exacte ou complète.",
        "Elle ne constitue ni une signature de la source ni une preuve juridique d'origine.",
        "La v1.5 ne fournit pas encore de bouton de recalcul ou de rapport d'intégrité historique.",
    ]))
    s.append(PageBreak())

    # 10
    add_page_title(s, "10. Module analytique R")
    s.append(P(
        "Le module R est isolé dans un profil Compose nommé analytics. Il peut être construit lors de l'installation ou ajouté plus tard en relançant l'installateur. Le cœur Python/PostGIS ne dépend pas de son démarrage."
    ))
    s.append(H2("10.1 Fonctions actuelles"))
    s.append(data_table([
        ["Route interne R", "Fonction"],
        ["GET /health", "Retourne status=ok, language=R et la version R"],
        ["GET /summary?values=...", "n, moyenne, écart-type, médiane, minimum et maximum"],
    ], [66 * mm, 108 * mm]))
    s.append(H2("10.2 Accès depuis HDP"))
    s.append(P(
        "FastAPI appelle seulement /health par l'intermédiaire de /api/analysis/status. Le port 8001 n'est pas publié sur Windows et /summary n'est pas encore relayé par l'API Python. L'interface web ne possède donc pas encore de panneau d'analyse."
    ))
    s.append(H2("10.3 Démarrage"))
    s.append(codebox("start-hdp-with-r.cmd"))
    s.append(P("Pour revenir au cœur seul, arrêter les services puis utiliser start-hdp.cmd. Le profil ne supprime pas les données PostgreSQL."))
    s.append(callout("Ressources", "La construction R télécharge des paquets supplémentaires et demande davantage de disque et de mémoire. Vérifier l'espace disponible avant de l'activer.", "warning"))
    s.append(PageBreak())

    # 11
    add_page_title(s, "11. Démarrage, arrêt et persistance")
    s.append(H2("11.1 Scripts fournis"))
    s.append(data_table([
        ["Script", "Effet"],
        ["start-hdp.cmd", "Démarre db et api, puis ouvre le port HDP_PORT"],
        ["start-hdp-with-r.cmd", "Démarre également le profil analytics"],
        ["stop-hdp.cmd", "Exécute docker compose --profile analytics down"],
    ], [64 * mm, 110 * mm]))
    s.append(P(
        "La commande down arrête et supprime les conteneurs et le réseau Compose, mais conserve par défaut le volume nommé postgres_data et le dossier data. Un redémarrage recrée les conteneurs avec les données existantes."
    ))
    s.append(H2("11.2 Réinstallation"))
    s.append(bullets([
        "Le payload applicatif est réécrit avec la version livrée.",
        "Le mot de passe PostgreSQL existant est conservé s'il est lisible dans .env.",
        "L'appname existant est conservé si aucun nouvel appname n'est fourni.",
        "HDP_PORT est recalculé si le port configuré est devenu indisponible.",
        "Le volume PostgreSQL et les images Docker ne sont pas purgés.",
    ]))
    s.append(callout("Ne pas confondre", "Réinstaller HDP n'est pas équivalent à Reset to factory defaults ou Clean/Purge data dans Docker Desktop. Ces actions Docker peuvent supprimer des données et ne sont jamais nécessaires pour une relance normale.", "danger"))
    s.append(PageBreak())

    # 12
    add_page_title(s, "12. Sauvegarde et restauration")
    s.append(H2("12.1 Eléments à sauvegarder"))
    s.append(bullets([
        "Le dossier data contenant les JSON archivés.",
        "Un export SQL de la base acquisitions.",
        "Le fichier .env, à conserver comme secret et à ne pas transmettre dans un diagnostic.",
        "Les sources et l'installateur correspondant à la version utilisée.",
    ]))
    s.append(H2("12.2 Sauvegarde SQL simple"))
    s.append(P("Depuis l'Invite de commandes Windows, dans le dossier HumanitarianDataPlatform :"))
    s.append(codebox("docker compose exec -T db pg_dump -U humanitarian -d humanitarian --no-owner --no-privileges > humanitarian_backup.sql"))
    s.append(P("Copier ensuite data, humanitarian_backup.sql et .env vers un emplacement protégé. Le fichier .env contient un secret."))
    s.append(H2("12.3 Restauration"))
    s.append(P(
        "Une restauration écrase ou fusionne potentiellement des objets SQL. Elle doit être testée sur une copie. Arrêter les acquisitions, conserver une sauvegarde du volume actuel et utiliser une procédure PostgreSQL adaptée au contexte. Pour une base vide, la commande suivante peut être utilisée depuis cmd.exe :"
    ))
    s.append(codebox("docker compose exec -T db psql -U humanitarian -d humanitarian < humanitarian_backup.sql"))
    s.append(callout("Prudence", "Ne jamais exécuter docker compose down -v pour dépanner ou restaurer tant qu'une sauvegarde vérifiée du volume PostgreSQL n'existe pas.", "danger"))
    s.append(PageBreak())

    # 13
    add_page_title(s, "13. Sécurité, confidentialité et conditions d'usage")
    s.append(H2("13.1 Protections présentes"))
    s.append(bullets([
        "Publication de l'API sur la boucle locale 127.0.0.1.",
        "Aucun port PostgreSQL publié sur Windows.",
        "Mot de passe PostgreSQL généré aléatoirement.",
        "Empreinte SHA-256 des acquisitions.",
        "Ouverture des liens externes avec rel=noopener.",
    ]))
    s.append(H2("13.2 Limites de sécurité"))
    s.append(bullets([
        "Pas d'authentification ni de séparation des utilisateurs.",
        "HTTP local sans TLS.",
        "Secrets et fichiers JSON stockés en clair sur le disque Windows.",
        "Pas de chiffrement applicatif, d'audit de sécurité ou de rotation des secrets.",
        "Pas de politique de mise à jour automatique de HDP ou de ses images.",
        "L'accès au moteur Docker confère des privilèges importants sur la machine.",
    ]))
    s.append(H2("13.3 Données distantes"))
    s.append(P(
        "Les mots-clés sont envoyés à ReliefWeb ou HDX. ReliefWeb peut journaliser les appels associés à l'appname. Les contenus peuvent appartenir à leurs producteurs. L'utilisateur doit respecter les conditions, quotas, licences et droits de propriété intellectuelle de chaque source."
    ))
    s.append(H2("13.4 Licence du projet"))
    s.append(P(
        "L'archive source v1.5 ne contient pas de fichier de licence HDP explicite. Il ne faut donc pas déduire automatiquement un droit de redistribution ou une licence open source. Une licence devra être choisie et ajoutée avant diffusion publique."
    ))
    s.append(PageBreak())

    # 14
    add_page_title(s, "14. Diagnostic et dépannage")
    s.append(H2("14.1 Produire un diagnostic"))
    s.append(bullets([
        "Double-cliquer sur HDP_Diagnostic_v1.5.cmd.",
        "Attendre la fin des contrôles, chacun étant limité à 15 secondes.",
        "Récupérer HDP_Debug_v1.5_*.log sur le Bureau.",
        "Joindre ce fichier sans ajouter manuellement le contenu de .env.",
    ]))
    s.append(P(
        "Le diagnostic recense Windows, l'espace disque, les programmes, WSL, Docker, les contextes, les ports en écoute, les services Compose et leurs journaux. Il n'affiche volontairement que HDP_PORT dans .env."
    ))
    s.append(H2("14.2 Tableau de résolution"))
    s.append(data_table([
        ["Symptôme", "Cause probable", "Action"],
        ["Docker ne répond pas", "Premier démarrage, WSL ou conditions Docker", "Ouvrir Docker, terminer l'assistant, vérifier wsl --version"],
        ["Attente puis arrêt à 6 min", "Moteur Docker non prêt", "Redémarrer Windows/WSL si demandé, puis relancer HDP"],
        ["Port 8080 refusé", "Port occupé ou réservé", "La v1.5 choisit 18080-18279 ; lire HDP_PORT"],
        ["ReliefWeb HTTP 503", "Appname absent", "Obtenir et configurer un appname pré-approuvé"],
        ["Source distante HTTP 502", "Erreur réseau ou API distante", "Tester la connexion, le proxy et réessayer plus tard"],
        ["R not_started", "Profil analytics non lancé", "Utiliser start-hdp-with-r.cmd ou réinstaller avec R"],
        ["Disque presque plein", "Images, cache ou données", "Libérer de l'espace ou déplacer le disque Docker"],
        ["Navigateur non ouvert", "Association navigateur ou lancement bloqué", "Lire HDP_PORT et ouvrir localhost manuellement"],
    ], [43 * mm, 55 * mm, 76 * mm]))
    s.append(PageBreak())

    # 15
    add_page_title(s, "15. Lecture des journaux et faux positifs connus")
    s.append(H2("15.1 Messages normaux PostgreSQL"))
    s.append(bullets([
        "initdb: warning: enabling trust authentication for local connections pendant l'initialisation du conteneur.",
        "received fast shutdown request lors du redémarrage contrôlé après l'initialisation.",
        "logical replication launcher exited with exit code 1 pendant ce même arrêt rapide.",
        "database system is ready to accept connections confirme ensuite le démarrage normal.",
    ]))
    s.append(H2("15.2 Défauts cosmétiques du diagnostic v1.5"))
    s.append(P(
        "Certaines lignes [code de sortie :] peuvent rester vides et certaines commandes Windows peuvent produire des caractères mal décodés. Ces anomalies appartiennent au script de collecte et n'indiquent pas nécessairement une panne de HDP. Le statut Compose, les healthchecks et les réponses HTTP sont prioritaires pour conclure."
    ))
    s.append(H2("15.3 Critères d'un démarrage réussi"))
    s.append(codebox("api    Up ... (healthy)    127.0.0.1:<HDP_PORT>->8080/tcp\ndb     Up ... (healthy)    5432/tcp\nGET /api/health HTTP/1.1 200 OK"))
    s.append(callout("Diagnostic v1.5 du 7 août 2026", "Ces trois critères sont présents. L'installation et le démarrage de l'application sont donc démontrés sur la machine testée.", "success"))
    s.append(PageBreak())

    # 16
    add_page_title(s, "16. Désinstallation")
    s.append(H2("16.1 Retirer l'application tout en conservant les données"))
    s.append(bullets([
        "Exécuter stop-hdp.cmd.",
        "Sauvegarder data, .env et un export SQL.",
        "Conserver le dossier ou l'archive de sauvegarde.",
        "Docker Desktop, Git et Visual Studio Code restent installés ; ils se gèrent séparément.",
    ]))
    s.append(H2("16.2 Suppression complète des données HDP"))
    s.append(P(
        "La commande suivante détruit le volume PostgreSQL du projet. Elle est irréversible sans sauvegarde et ne doit être utilisée que si la suppression complète est explicitement souhaitée :"
    ))
    s.append(codebox("docker compose --profile analytics down -v"))
    s.append(P(
        "Après vérification de la sauvegarde, supprimer manuellement le dossier %USERPROFILE%\\HumanitarianDataPlatform pour retirer le code, .env et les JSON. Les images Docker peuvent être utilisées par d'autres projets ; ne pas les purger automatiquement."
    ))
    s.append(callout("Action destructive", "Ne jamais utiliser down -v, Clean/Purge data ou Reset to factory defaults comme première mesure de dépannage.", "danger"))
    s.append(PageBreak())

    # 17
    add_page_title(s, "17. Historique des versions et validation")
    s.append(data_table([
        ["Version", "Incident principal", "Correction structurante"],
        ["1.1", "HTA/Internet Explorer, JSON indéfini, absence d'effet visible", "Abandon de l'ancien moteur HTA"],
        ["1.2", "Gel apparent et défilement insuffisant", "Interface Win32 native, travail séparé de l'interface"],
        ["1.3", "Sorties Docker trop volumineuses", "Sorties limitées, activité visible, R facultatif"],
        ["1.4", "Sonde Docker elle-même bloquante", "Sondes de 5 s, attente 6 min, contrôle WSL"],
        ["1.5", "Refus du port Windows 8080", "Port automatique 18080-18279 et configuration partagée"],
    ], [22 * mm, 69 * mm, 83 * mm]))
    s.append(H2("17.1 Contrôles de construction v1.5"))
    s.append(bullets([
        "Compilation croisée Zig sans avertissement avec -Wall -Wextra -Werror.",
        "Binaire PE32+ x86-64 avec sous-système Windows GUI.",
        "Analyse syntaxique Python et parsing YAML Compose réussis.",
        "Douze fichiers du payload reconstruits à l'identique depuis l'en-tête embarqué.",
        "Archives ZIP testées sans erreur.",
        "Empreinte de l'exécutable vérifiée dans l'archive Windows.",
    ]))
    s.append(H2("17.2 Validation Windows observée"))
    s.append(data_table([
        ["Elément", "Valeur observée le 7 août 2026"],
        ["Windows", "Windows 11 Professionnel x64, build 26200.8875"],
        ["WSL", "2.6.3.0, noyau 6.6.87.2"],
        ["Docker", "Desktop 4.61.0, moteur 29.2.1, contexte desktop-linux"],
        ["Port HDP", "18080"],
        ["Services", "api healthy, db healthy"],
        ["HTTP", "/ et /api/health en 200 OK"],
        ["Disque C:", "13,8 Gio libres"],
    ], [44 * mm, 130 * mm]))
    s.append(PageBreak())

    # 18
    add_page_title(s, "18. Feuille de route recommandée")
    s.append(data_table([
        ["Priorité", "Evolution", "Critère de réussite"],
        ["1", "Tests fonctionnels du MVP", "Connecteurs, provenance et persistance testés automatiquement"],
        ["2", "Historique dans l'interface", "Lister, filtrer et ouvrir les acquisitions"],
        ["3", "Ressources HDX", "Sélection et téléchargement contrôlé avec licence et checksum"],
        ["4", "Migrations et provenance", "Schéma versionné, statuts, erreurs et métadonnées enrichies"],
        ["5", "Planification", "Tâches reprises après erreur, quotas et journal d'exécution"],
        ["6", "Normalisation", "Modèle commun documenté et conservation du brut"],
        ["7", "PostGIS et carte", "Géométries validées et visualisation locale"],
        ["8", "Analyses R", "Endpoints derrière FastAPI et interface analytique"],
        ["9", "Nouvelles sources", "HAPI, OMS et autres connecteurs testés"],
        ["10", "Mode serveur séparé", "TLS, identité, secrets, sauvegardes et supervision"],
    ], [19 * mm, 59 * mm, 96 * mm]))
    s.append(callout(
        "Règle d'évolution",
        "Chaque nouvelle fonction doit conserver le JSON source, documenter sa transformation, tester la provenance et ne pas exposer de service interne directement pour contourner FastAPI.",
        "info",
    ))
    s.append(PageBreak())

    # 19
    add_page_title(s, "19. Références officielles")
    references = [
        ("Docker Desktop - installation Windows et prérequis", "https://docs.docker.com/desktop/setup/install/windows-install/"),
        ("Docker Desktop - backend WSL 2 et emplacement des données", "https://docs.docker.com/desktop/features/wsl/"),
        ("Docker Compose - profils", "https://docs.docker.com/compose/how-tos/profiles/"),
        ("Docker - volumes", "https://docs.docker.com/engine/storage/volumes/"),
        ("Microsoft - Windows Package Manager / winget", "https://learn.microsoft.com/en-us/windows/package-manager/winget/"),
        ("ReliefWeb API v2 - documentation", "https://apidoc.reliefweb.int/"),
        ("ReliefWeb - paramètres et appname", "https://apidoc.reliefweb.int/parameters"),
        ("CKAN 2.10 - API Action", "https://docs.ckan.org/en/2.10/api/"),
        ("FastAPI - fonctions et OpenAPI", "https://fastapi.tiangolo.com/features/"),
    ]
    for label, url in references:
        s.append(P(f'- <link href="{url}" color="#1479B8"><u>{label}</u></link><br/><font size="7.5" color="#5E6B78">{url}</font>'))
    s.append(Spacer(1, 4 * mm))
    s.append(P("Références consultées le 7 août 2026. Les prérequis, quotas, conditions et licences peuvent évoluer ; vérifier les pages officielles lors d'un nouveau déploiement."))
    s.append(H2("19.1 Sources internes de cette notice"))
    s.append(bullets([
        "Code source et payload Humanitarian Data Platform v1.5.0.",
        "HumanitarianDataPlatform_Setup_README_v1.5.txt.",
        "HDP_Diagnostic_v1.5.cmd.",
        "Journal HDP_Debug_v1.5_20260807_134201.log.",
        "Résultats de compilation, reconstruction du payload et vérification des archives.",
    ]))
    s.append(PageBreak())

    # 20
    add_page_title(s, "20. Aide-mémoire")
    s.append(H2("Adresses"))
    s.append(codebox("Interface :  http://localhost:<HDP_PORT>\nSanté :     http://localhost:<HDP_PORT>/api/health\nAPI :       http://localhost:<HDP_PORT>/docs\nHistorique : http://localhost:<HDP_PORT>/api/acquisitions"))
    s.append(H2("Fichiers"))
    s.append(codebox("Application : %USERPROFILE%\\HumanitarianDataPlatform\nConfiguration : %USERPROFILE%\\HumanitarianDataPlatform\\.env\nDonnées : %USERPROFILE%\\HumanitarianDataPlatform\\data\\raw\nLogs : %LOCALAPPDATA%\\HumanitarianDataPlatform\\logs\nDiagnostic : Bureau\\HDP_Debug_v1.5_*.log"))
    s.append(H2("Actions"))
    s.append(data_table([
        ["Besoin", "Action"],
        ["Démarrer", "Double-cliquer sur start-hdp.cmd"],
        ["Démarrer avec R", "Double-cliquer sur start-hdp-with-r.cmd"],
        ["Arrêter", "Double-cliquer sur stop-hdp.cmd"],
        ["Connaître le port", "Lire uniquement HDP_PORT dans .env"],
        ["Diagnostiquer", "Exécuter HDP_Diagnostic_v1.5.cmd"],
        ["Vérifier le service", "Ouvrir /api/health"],
        ["Sauvegarder", "Copier data, exporter PostgreSQL et protéger .env"],
    ], [54 * mm, 120 * mm]))
    s.append(Spacer(1, 8 * mm))
    s.append(callout(
        "Etat de référence",
        "La v1.5 est installée et opérationnelle sur http://localhost:18080 dans le diagnostic de référence. La prochaine étape est la validation fonctionnelle des acquisitions HDX et ReliefWeb, puis le développement de l'historique et des contrôles de provenance.",
        "success",
    ))
    s += [Spacer(1, 12 * mm), P("Fin de la notice - Humanitarian Data Platform v1.5.0", "center")]
    return s


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = HDPDocTemplate(str(OUTPUT))
    document.multiBuild(build_story())
    print(OUTPUT)


if __name__ == "__main__":
    main()
