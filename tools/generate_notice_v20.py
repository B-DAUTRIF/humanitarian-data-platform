from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "Notice_detaillee_Humanitarian_Data_Platform_v2.0.pdf"
NAVY = colors.HexColor("#07111F")
PANEL = colors.HexColor("#10243B")
BLUE = colors.HexColor("#0EA5E9")
INDIGO = colors.HexColor("#6366F1")
GREEN = colors.HexColor("#10B981")
AMBER = colors.HexColor("#F59E0B")
RED = colors.HexColor("#E11D48")
INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#53657A")
PALE = colors.HexColor("#EAF5FC")
LIGHT = colors.HexColor("#F5F8FB")
WHITE = colors.white


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=28, leading=32, textColor=WHITE, alignment=TA_LEFT, spaceAfter=10))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontName="Helvetica", fontSize=13, leading=19, textColor=colors.HexColor("#C9E8FA"), spaceAfter=8))
styles.add(ParagraphStyle(name="Section", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=21, leading=25, textColor=NAVY, spaceAfter=10))
styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INDIGO, spaceBefore=8, spaceAfter=5))
styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13.4, textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle(name="Smallx", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.7, leading=10.5, textColor=MUTED, spaceAfter=4))
styles.add(ParagraphStyle(name="Bulletx", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.1, leading=13.1, leftIndent=13, firstLineIndent=-7, bulletIndent=4, textColor=INK, spaceAfter=4))
styles.add(ParagraphStyle(name="Codex", parent=styles["Code"], fontName="Courier", fontSize=7.7, leading=10.5, textColor=colors.HexColor("#D8F3FF"), backColor=NAVY, borderPadding=8, spaceBefore=5, spaceAfter=7))
styles.add(ParagraphStyle(name="Centerx", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.5, leading=12, alignment=TA_CENTER, textColor=MUTED))


def P(text: str, style: str = "Bodyx") -> Paragraph:
    return Paragraph(text, styles[style])


def B(text: str) -> Paragraph:
    return Paragraph(f"• {text}", styles["Bulletx"])


def heading(number: str, title: str, intro: str) -> list:
    return [P(f"{number}. {title}", "Section"), P(intro), Spacer(1, 2 * mm)]


def table(rows: list[list[str]], widths: list[float] | None = None) -> Table:
    body = [[P(str(cell), "Smallx") for cell in row] for row in rows]
    result = Table(body, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), LIGHT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, WHITE]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CCD8E5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return result


def callout(title: str, body: str, color=BLUE) -> Table:
    box = Table([[P(f"<b>{title}</b><br/>{body}", "Bodyx")]], colWidths=[170 * mm])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("BOX", (0, 0), (-1, -1), 1.2, color), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return box


class Notice(BaseDocTemplate):
    def __init__(self, path: Path):
        super().__init__(str(path), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=19 * mm, bottomMargin=17 * mm, title="Notice détaillée - Humanitarian Data Platform 2.0", author="Humanitarian Data Platform", subject="Installation, usage, architecture, sécurité et validation")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="main")
        self.addPageTemplates(PageTemplate(id="normal", frames=[frame], onPage=self.decorate))

    @staticmethod
    def decorate(canvas, document) -> None:
        page = document.page
        canvas.saveState()
        if page == 1:
            canvas.setFillColor(NAVY)
            canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
            canvas.setFillColor(BLUE)
            canvas.circle(A4[0] - 28 * mm, A4[1] - 30 * mm, 42 * mm, fill=1, stroke=0)
            canvas.setFillColor(INDIGO)
            canvas.circle(A4[0] - 5 * mm, A4[1] - 63 * mm, 29 * mm, fill=1, stroke=0)
        else:
            canvas.setStrokeColor(colors.HexColor("#CBD8E5"))
            canvas.line(20 * mm, 14 * mm, A4[0] - 20 * mm, 14 * mm)
            canvas.setFont("Helvetica", 7.5)
            canvas.setFillColor(MUTED)
            canvas.drawString(20 * mm, 9 * mm, "HUMANITARIAN DATA PLATFORM — NOTICE v2.0")
            canvas.drawRightString(A4[0] - 20 * mm, 9 * mm, f"Page {page}")
        canvas.restoreState()


def build_story() -> list:
    s: list = []
    s += [Spacer(1, 40 * mm), P("HUMANITARIAN<br/>DATA PLATFORM", "CoverTitle"), P("Notice détaillée — version 2.0.0", "CoverSub"), Spacer(1, 8 * mm), P("Projets · téléchargements automatiques · planifications · données locales", "CoverSub"), Spacer(1, 55 * mm), P("Windows 10/11 x64 · application locale", "CoverSub"), P("Édition du 7 août 2026", "CoverSub"), PageBreak()]

    s += heading("1", "Résumé exécutif", "HDP 2.0 transforme le socle d'acquisition 1.5 en espace de travail organisé par projets. La réponse distante reste toujours archivée ; les fichiers référencés peuvent maintenant être téléchargés, inventoriés et contrôlés.")
    s += [table([["Capacité", "Résultat livré"], ["Projets", "Séparation des ressources, préférences, scripts et planifications"], ["Automatisation", "Planificateur PostgreSQL persistant, minimum 15 minutes"], ["Ressources", "Téléchargement optionnel, limites, SHA-256 et suppression contrôlée"], ["Compatibilité", "Migration idempotente des acquisitions 1.5 vers le projet par défaut"], ["Documentation", "Markdown GitHub, Swagger local et présente notice PDF"]], [43 * mm, 127 * mm]), Spacer(1, 5 * mm), callout("Positionnement", "Application locale mono-utilisateur. Ce n'est ni un serveur Internet durci, ni un moteur d'exécution de scripts.", AMBER), PageBreak()]

    s += heading("2", "Contenu fonctionnel", "Cinq rubriques structurent l'interface web locale.")
    for text in ["<b>Recherche</b> : acquisition HDX/CKAN ou ReliefWeb et téléchargement optionnel.", "<b>Projets & préférences</b> : création, sélection, limites et formats.", "<b>Données locales</b> : compteurs, inventaire, remise au navigateur, intégrité et suppression.", "<b>Scripts</b> : bibliothèque de contenu par projet, sans exécution.", "<b>Planifications</b> : création, suspension, exécution immédiate et archivage."]:
        s.append(B(text))
    s += [Spacer(1, 4 * mm), callout("Traçabilité", "Une erreur de téléchargement ne supprime pas l'acquisition : le JSON brut, sa date UTC et son empreinte restent disponibles."), PageBreak()]

    s += heading("3", "Prérequis et installation", "L'installateur natif x64 déploie le payload, vérifie Docker et ouvre l'interface sur un port local disponible.")
    s += [table([["Prérequis", "Recommandation"], ["Système", "Windows 10 ou 11 x64"], ["Docker", "Docker Desktop avec WSL 2 opérationnel"], ["Disque", "10 Gio libres ou plus"], ["Réseau", "Accès aux images Docker et aux sources choisies"], ["ReliefWeb", "Appname pré-approuvé si cette source est utilisée"]], [45 * mm, 125 * mm]), P("Get-FileHash .\\HumanitarianDataPlatform_Setup_Native_GUI_v2.0.exe -Algorithm SHA256", "Codex"), B("Comparer la valeur au fichier `.exe.sha256`."), B("Lancer l'EXE ; conserver le dossier proposé pour une mise à niveau."), B("Ne sélectionner les logiciels tiers et R que s'ils sont souhaités."), PageBreak()]

    s += heading("4", "Mise à niveau depuis 1.5", "La migration préserve les fichiers et complète le schéma PostgreSQL au premier démarrage.")
    s += [table([["Conservé", "Traitement 2.0"], ["`.env`", "Secret PostgreSQL, port et appname réutilisés"], ["Volume PostgreSQL", "Nouvelles tables et colonnes ajoutées"], ["Acquisitions", "Rattachées au Projet par défaut"], ["JSON bruts", "Chemins historiques laissés inchangés"], ["Dossier `data`", "Conservé ; nouveaux sous-dossiers par projet"]], [47 * mm, 123 * mm]), Spacer(1, 5 * mm), callout("Sauvegarde", "Sauvegarder `.env`, `data/` et le volume PostgreSQL avant une mise à niveau importante. Ne jamais partager `.env`.", AMBER), PageBreak()]

    s += heading("5", "Gestion des projets", "Le projet actif est le périmètre de toutes les rubriques.")
    s += [B("Créer un nom et une description explicites."), B("Sélectionner le projet dans l'en-tête avant une recherche."), B("Définir ses préférences de téléchargement."), B("Archiver un projet secondaire sans supprimer ses fichiers."), B("Le Projet par défaut est protégé contre l'archivage."), Spacer(1, 4 * mm), table([["Objet", "Appartenance"], ["Acquisition", "Un seul projet"], ["Ressource", "Projet et acquisition d'origine"], ["Script", "Un seul projet"], ["Planification", "Un seul projet, avec historique"]], [55 * mm, 115 * mm]), PageBreak()]

    s += heading("6", "Préférences de téléchargement", "Les limites s'appliquent aux acquisitions manuelles et planifiées.")
    s += [table([["Préférence", "Plage ou sens"], ["Téléchargement par défaut", "Désactivé à l'installation"], ["Taille par fichier", "1 Mio à 2 Gio ; défaut 100 Mio"], ["Quantité", "1 à 100 ; défaut 20"], ["Formats", "Liste normalisée ; vide = tous"]], [56 * mm, 114 * mm]), Spacer(1, 5 * mm), P("Une ressource au-delà de la quantité maximale est comptée comme ignorée. Un format exclu n'est pas ouvert. Une taille déclarée ou réellement reçue au-delà de la limite interrompt le flux et supprime le fichier `.part`.") , PageBreak()]

    s += heading("7", "Acquisition et sources", "HDP utilise ReliefWeb V2 et l'Action API CKAN de HDX.")
    s += [table([["Source", "Recherche", "Ressources"], ["HDX / CKAN", "`package_search`", "Tableau `resources` et champ URL"], ["ReliefWeb", "Rapports V2, profil complet", "Fichiers présents dans les métadonnées"]], [38 * mm, 55 * mm, 77 * mm]), Spacer(1, 5 * mm), P("L'Action API CKAN peut répondre en HTTP 200 tout en indiquant `success: false`; HDP contrôle donc aussi cet indicateur."), P("ReliefWeb exige un appname pré-approuvé. Sans valeur, l'API locale retourne une erreur 503 explicite et HDX reste accessible."), P("Références officielles : <link href='https://docs.ckan.org/en/latest/api/' color='#0EA5E9'>CKAN API</link> · <link href='https://apidoc.reliefweb.int/' color='#0EA5E9'>ReliefWeb API</link> · <link href='https://apidoc.reliefweb.int/parameters' color='#0EA5E9'>paramètres ReliefWeb</link>."), PageBreak()]

    s += heading("8", "Téléchargement sécurisé", "Chaque ressource est téléchargée séquentiellement avec une enveloppe de sécurité locale.")
    for text in ["URL initiale et redirections limitées à HTTP(S).", "Identifiants intégrés à l'URL interdits.", "Résolution DNS et refus des IP privées, locales, réservées ou non globales.", "Nom de fichier neutralisé pour Windows et chemin confiné sous `data/`.", "Limite contrôlée avant et pendant le flux.", "Écriture `.part`, calcul SHA-256 progressif, puis renommage atomique."]:
        s.append(B(text))
    s += [Spacer(1, 4 * mm), callout("Limite", "Ce filtrage réduit les risques mais ne remplace pas une isolation réseau, un antivirus ou un audit de sécurité indépendant.", AMBER), PageBreak()]

    s += heading("9", "Données locales", "La rubrique dédiée fournit un inventaire opérationnel des fichiers du projet.")
    s += [table([["Action", "Effet"], ["Actualiser", "Recalcule l'affichage depuis PostgreSQL"], ["Télécharger", "Transmet le fichier local au navigateur"], ["Vérifier SHA-256", "Relit le fichier par blocs et compare l'empreinte"], ["Supprimer localement", "Demande confirmation, efface le fichier, marque `deleted`"]], [51 * mm, 119 * mm]), Spacer(1, 5 * mm), P("La suppression ne retire ni l'acquisition ni la ligne de ressource. Cette décision conserve la provenance et permet d'expliquer qu'un fichier a existé puis a été supprimé."), PageBreak()]

    s += heading("10", "Planifications", "Une planification persiste sa requête, ses limites et son prochain passage dans PostgreSQL.")
    s += [B("Intervalle de 15 minutes à 30 jours."), B("Activation, suspension, exécution immédiate et archivage."), B("Téléchargement automatique indépendant pour chaque planification."), B("Historique : début, fin, statut, acquisition et erreur éventuelle."), B("Réservation transactionnelle avec `FOR UPDATE SKIP LOCKED`."), Spacer(1, 4 * mm), callout("Quotas", "Le minimum technique de 15 minutes n'est pas une recommandation universelle. Calculez la fréquence selon le quota et le nombre de planifications, notamment pour ReliefWeb.", AMBER), PageBreak()]

    s += heading("11", "Scripts par projet", "HDP 2.0 gère le contenu des scripts sans fournir de route d'exécution.")
    s += [table([["Champ", "Usage"], ["Nom", "Identification dans le projet"], ["Langage", "Python, R, SQL, shell ou autre"], ["Description", "Finalité et prérequis"], ["Contenu", "Texte jusqu'à 500 000 caractères"], ["Archivage", "Retrait de la liste active"]], [45 * mm, 125 * mm]), Spacer(1, 5 * mm), callout("Barrière de sécurité", "Aucune planification ne peut exécuter un script. Toute future exécution devra introduire isolation, autorisations, limites de ressources et journalisation.", GREEN), PageBreak()]

    s += heading("12", "Architecture technique", "Le payload installé combine FastAPI, PostgreSQL/PostGIS et une interface HTML autonome.")
    s += [table([["Composant", "Rôle"], ["Installateur C/Win32", "Déploiement, prérequis, port, journaux et ouverture"], ["FastAPI / Uvicorn", "API, interface, connecteurs et planificateur"], ["httpx", "Appels HTTPS et flux de ressources"], ["PostgreSQL/PostGIS", "Projets, provenance, préférences et historique"], ["Fichiers Windows", "JSON bruts et ressources"], ["R / plumber", "Service analytique facultatif"]], [49 * mm, 121 * mm]), P("API : 127.0.0.1:${HDP_PORT} → conteneur 8080\nBase : réseau Compose uniquement\nR : profil analytics, réseau Compose uniquement", "Codex"), PageBreak()]

    s += heading("13", "Modèle de données", "Les tables principales assurent l'isolation par projet et la traçabilité.")
    s += [table([["Table", "Identité et relations"], ["projects", "UUID, nom, description, dates, archivage"], ["project_preferences", "Une ligne JSONB par projet"], ["acquisitions", "Projet, planification facultative, source, requête, hash"], ["local_resources", "Projet, acquisition, URL, chemin, taille, hash, statut"], ["project_scripts", "Projet, langage, contenu et archivage"], ["schedules", "Projet, fréquence, prochain passage et dernier état"], ["schedule_runs", "Planification, acquisition, statut et erreur"]], [48 * mm, 122 * mm]), PageBreak()]

    s += heading("14", "API locale", "Swagger UI est disponible sur `/docs`; les routes d'acquisition ont des effets persistants.")
    s += [table([["Groupe", "Routes essentielles"], ["Projets", "GET/POST `/api/projects`; PATCH/DELETE `/api/projects/{id}`"], ["Préférences", "GET/PUT `/api/projects/{id}/preferences`"], ["Acquisition", "GET `/api/search`; GET `/api/acquisitions`"], ["Ressources", "GET `/api/resources`; file, verify et DELETE"], ["Scripts", "GET/POST par projet ; PATCH/DELETE par script"], ["Planifications", "GET/POST par projet ; PATCH, run, runs et DELETE"], ["Système", "health, sources, analysis/status, docs, openapi.json"]], [48 * mm, 122 * mm]), Spacer(1, 4 * mm), P("`GET /api/search` crée une acquisition malgré la méthode GET héritée de la version 1.5. Ne l'utilisez pas comme sonde de santé."), PageBreak()]

    s += heading("15", "Sécurité et confidentialité", "Le principal périmètre de confiance est la session Windows locale.")
    for text in ["Ne pas exposer le port HTTP hors de `127.0.0.1`.", "Ne jamais publier `.env`, qui contient le secret PostgreSQL.", "Relire les journaux avant partage.", "Ne pas ingérer de données personnelles ou confidentielles sans évaluation.", "Analyser les fichiers téléchargés selon la politique de l'organisation.", "Vérifier les empreintes des livrables ; l'installateur n'est pas signé."]:
        s.append(B(text))
    s += [Spacer(1, 5 * mm), callout("Licence", "Aucune licence HDP explicite n'est incluse. Le dépôt doit rester privé tant qu'une licence n'a pas été choisie.", RED), PageBreak()]

    s += heading("16", "Exploitation et sauvegarde", "L'arrêt normal conserve les fichiers et le volume PostgreSQL.")
    s += [P("%USERPROFILE%\\HumanitarianDataPlatform\\.env\n%USERPROFILE%\\HumanitarianDataPlatform\\data\\raw\n%USERPROFILE%\\HumanitarianDataPlatform\\data\\projects\n%LOCALAPPDATA%\\HumanitarianDataPlatform\\logs", "Codex"), B("Utiliser `stop-hdp.cmd` pour arrêter les services."), B("Sauvegarder `.env`, `data/` et le volume PostgreSQL ensemble."), B("Ne pas utiliser `docker compose down -v`, Clean/Purge data ou Reset to factory defaults sans intention explicite."), B("Surveiller l'espace disque avant d'activer des planifications de téléchargement."), PageBreak()]

    s += heading("17", "Diagnostic", "Le script v2.0 collecte un état borné et crée un journal sur le Bureau.")
    s += [P("HDP_Diagnostic_v2.0.cmd", "Codex"), table([["Contrôle", "Contenu"], ["Windows", "Version, architecture et espace disque"], ["Outils", "winget, Docker, WSL, Git, VS Code"], ["Réseau", "Ports écoutés et plages exclues"], ["HDP", "Services, journaux et arborescences de données"], ["Secret", "Seul HDP_PORT est lu depuis `.env`"]], [45 * mm, 125 * mm]), Spacer(1, 5 * mm), P("Chaque commande externe est interrompue après 15 secondes. Le journal peut néanmoins contenir des noms de machine, d'utilisateur ou des chemins : le relire avant envoi."), PageBreak()]

    s += heading("18", "Construction et contrôles", "Les validations ci-dessous accompagnent la remise 2.0.")
    s += [table([["Contrôle", "Attendu"], ["Python", "Compilation des modules et tests unitaires"], ["JavaScript", "Analyse syntaxique du script de l'interface"], ["Payload", "14 fichiers reconstruits, comparaison exacte"], ["Windows", "PE32+ GUI x86-64"], ["ZIP", "Test d'intégrité des trois archives"], ["SHA-256", "Contrôle de tous les livrables v2.0"], ["PDF", "Rendu en images et extraction du texte"]], [48 * mm, 122 * mm]), Spacer(1, 4 * mm), callout("Recette Docker", "La migration PostgreSQL/PostGIS et le parcours navigateur complet nécessitent Docker. Ils ne doivent pas être déclarés réussis lorsqu'ils n'ont pas été exécutés.", AMBER), PageBreak()]

    s += heading("19", "Limites et évolutions", "La version 2.0 privilégie la traçabilité et des barrières simples.")
    for text in ["Un seul processus Uvicorn est supposé pour le planificateur.", "Pas d'authentification, de multi-utilisateur ou de serveur distant.", "Pas d'exécution de scripts, de dépendances de scripts ni de bac à sable.", "Pas de reprise partielle d'un gros téléchargement interrompu.", "Pas d'analyse antivirus ni de validation métier des ressources.", "Pas de calendrier cron complexe, seulement un intervalle en minutes."]:
        s.append(B(text))
    s += [Spacer(1, 5 * mm), P("Évolutions possibles : file de tâches dédiée, quotas journaliers visibles, rétentions automatiques, export/import de projet, permissions et exécution isolée des scripts."), PageBreak()]

    s += heading("20", "Livrables et checklist", "La remise conserve la version 1.5 et ajoute un ensemble v2.0 autonome.")
    s += [table([["Livrable", "Usage"], ["EXE + `.sha256`", "Installation Windows"], ["Windows ZIP", "Paquet utilisateur"], ["Source ZIP", "Reconstruction et audit"], ["Archive complète ZIP + hash", "Conservation de la remise"], ["README et diagnostic", "Démarrage et support"], ["Notice PDF", "Référence hors ligne"], ["Prompt de reprise", "Transmission du contexte technique"]], [52 * mm, 118 * mm]), Spacer(1, 5 * mm)]
    for text in ["Vérifier l'empreinte de l'EXE.", "Sauvegarder les données avant mise à niveau.", "Conserver l'application sur localhost.", "Configurer les limites avant le téléchargement automatique.", "Respecter quotas et licences des sources.", "Consulter `docs/` et `/docs` pour le détail."]:
        s.append(B(text))
    s += [Spacer(1, 8 * mm), P("Fin de la notice — Humanitarian Data Platform 2.0.0", "Centerx")]
    return s


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    Notice(OUTPUT).build(build_story())
    print(OUTPUT)


if __name__ == "__main__":
    main()
