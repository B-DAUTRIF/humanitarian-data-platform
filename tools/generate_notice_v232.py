#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "Notice_detaillee_Humanitarian_Data_Platform_v2.3.2.pdf"
PAGE_W, PAGE_H = A4
NAVY = colors.HexColor("#07111F")
PANEL = colors.HexColor("#10243A")
CYAN = colors.HexColor("#21B6E8")
BLUE = colors.HexColor("#5174F0")
TEXT = colors.HexColor("#17243A")
MUTED = colors.HexColor("#596B82")
PALE = colors.HexColor("#EAF6FB")
LINE = colors.HexColor("#D4E2EB")


def register_fonts() -> tuple[str, str]:
    regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if regular.is_file() and bold.is_file():
        pdfmetrics.registerFont(TTFont("HDP", regular))
        pdfmetrics.registerFont(TTFont("HDP-Bold", bold))
        return "HDP", "HDP-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()
styles = getSampleStyleSheet()
BODY = ParagraphStyle(
    "Body", parent=styles["BodyText"], fontName=FONT, fontSize=9.2, leading=13.2,
    textColor=TEXT, spaceAfter=7 * mm, alignment=TA_LEFT,
)
LEAD = ParagraphStyle(
    "Lead", parent=BODY, fontSize=12, leading=17, textColor=MUTED, spaceAfter=8 * mm,
)
H2 = ParagraphStyle(
    "H2", parent=BODY, fontName=FONT_BOLD, fontSize=12.2, leading=16,
    textColor=colors.HexColor("#0A688A"), spaceBefore=2 * mm, spaceAfter=3 * mm,
)
BULLET = ParagraphStyle(
    "Bullet", parent=BODY, leftIndent=5 * mm, firstLineIndent=-3 * mm,
    bulletIndent=1 * mm, spaceAfter=2.5 * mm,
)
SMALL = ParagraphStyle(
    "Small", parent=BODY, fontSize=7.8, leading=10.5, textColor=MUTED, spaceAfter=2 * mm,
)


PAGES: list[tuple[str, str, list[tuple[str, str]]]] = [
    (
        "Humanitarian Data Platform 2.3.2",
        "Notice détaillée d'installation, d'exploitation et de sécurité",
        [
            ("lead", "Édition du 7 août 2026 · application locale Windows x64 · documentation de remise"),
            ("h2", "Objet"),
            ("body", "HDP acquiert des métadonnées humanitaires publiques, conserve leur provenance et télécharge des ressources dans des espaces séparés par projet. La version 2.3.2 corrige la découverte des COD-AB officiels dans l'API CKAN actuelle et empêche l'affichage du statut d'un ancien périmètre."),
            ("h2", "Principes de remise"),
            ("bullet", "Un installateur Windows natif, trois archives ZIP, les sources, une documentation Markdown consultable sur GitHub, les empreintes SHA-256 et cette notice PDF."),
            ("bullet", "Aucun fichier utilisateur, volume PostgreSQL ou secret existant n'est supprimé pendant la mise à niveau."),
            ("bullet", "L'application reste liée à 127.0.0.1 et n'est pas conçue pour être exposée directement à Internet."),
        ],
    ),
    (
        "1. Résultat fonctionnel",
        "Ce que fournit la version 2.3.2",
        [
            ("lead", "Les fonctions 2.3.1 sont conservées ; la sélection officielle reste fermée aux jeux arbitraires et devient compatible avec les réponses CKAN sans dataseries_name."),
            ("bullet", "Projets : ressources, préférences, scripts, planifications, paramètres GitHub et profil géographique isolés."),
            ("bullet", "Téléchargement : contrôles de format, quantité, taille, adresse réseau et empreinte SHA-256."),
            ("bullet", "GitHub : propriétaire, nom, description, visibilité, création réelle après confirmation et mémorisation de l'URL."),
            ("bullet", "Géographie : périmètre ONU M49, COD-AB officiels, format géospatial et synchronisation manuelle ou périodique."),
            ("bullet", "Cohérence : tout changement de périmètre, politique ou format invalide l'ancien statut et demande une nouvelle synchronisation."),
            ("body", "Les scripts sont conservés comme contenu éditable mais ne sont jamais exécutés. Le dépôt GitHub nouvellement créé est initialisé avec un README par GitHub ; HDP ne lui envoie automatiquement aucune donnée locale."),
        ],
    ),
    (
        "2. Architecture locale",
        "Composants et frontières réseau",
        [
            ("body", "Docker Compose orchestre FastAPI, PostgreSQL/PostGIS et, en option, R/plumber. Seul FastAPI est publié sur Windows, exclusivement sur l'interface de boucle locale."),
            ("bullet", "API et interface : port 8080 si disponible, sinon premier port libre de 18080 à 18279."),
            ("bullet", "Base : volume Docker nommé, non publié sur l'hôte."),
            ("bullet", "Fichiers : data/raw pour les métadonnées et data/projects pour les ressources."),
            ("bullet", "Sorties distantes : HDX, ReliefWeb lorsque configuré, et GitHub lors d'une création demandée."),
            ("body", "Le planificateur s'exécute dans l'unique processus API. Une exploitation multi-worker nécessiterait un service de tâches dédié afin de conserver une revendication robuste des travaux."),
        ],
    ),
    (
        "3. Installation Windows",
        "Parcours recommandé",
        [
            ("bullet", "Décompresser HumanitarianDataPlatform_Windows_v2.3.2.zip."),
            ("bullet", "Calculer le SHA-256 de l'exécutable et le comparer au fichier .sha256 livré."),
            ("bullet", "Lancer l'installateur et conserver %USERPROFILE%\\HumanitarianDataPlatform pour une mise à niveau."),
            ("bullet", "Renseigner seulement les paramètres utiles, puis cocher explicitement les composants tiers souhaités."),
            ("bullet", "Attendre que Docker Desktop soit opérationnel et que l'interface locale s'ouvre."),
            ("body", "L'installateur est natif Win32, reste réactif pendant les opérations longues et journalise les étapes dans %LOCALAPPDATA%\\HumanitarianDataPlatform\\logs. Il n'est pas signé par un certificat d'éditeur."),
        ],
    ),
    (
        "4. Configuration et secrets",
        "Le fichier .env est local et sensible",
        [
            ("bullet", "POSTGRES_PASSWORD : généré aléatoirement et préservé lors des mises à niveau."),
            ("bullet", "RELIEFWEB_APPNAME : facultatif, doit être pré-approuvé par ReliefWeb."),
            ("bullet", "GITHUB_TOKEN : facultatif, saisi dans un champ masqué ou ajouté manuellement."),
            ("bullet", "HDP_PORT : port local choisi automatiquement et réutilisé lorsqu'il reste disponible."),
            ("body", "Le jeton GitHub n'est ni écrit dans les tables de projet, ni renvoyé par l'API, ni affiché dans l'interface ou le diagnostic. Un champ vide de l'installeur conserve la valeur déjà présente."),
            ("body", "Ne publiez jamais .env. Appliquez des droits de fichier adaptés au compte Windows et révoquez les jetons qui ne sont plus nécessaires."),
        ],
    ),
    (
        "5. Gestion des projets",
        "Contexte fonctionnel unique",
        [
            ("body", "Le sélecteur supérieur détermine le projet actif. Toutes les opérations et listes de l'interface utilisent cet identifiant."),
            ("bullet", "Le Projet par défaut reçoit les acquisitions migrées et ne peut pas être archivé."),
            ("bullet", "Un projet peut être archivé sans supprimer ses fichiers. Ses planifications et sa synchronisation géographique sont désactivées."),
            ("bullet", "Les paramètres GitHub contiennent uniquement des métadonnées non secrètes."),
            ("bullet", "Les préférences générales continuent de borner le téléchargement géographique."),
            ("body", "La suppression matérielle d'un volume ou du dossier data ne fait pas partie des opérations normales de l'application."),
        ],
    ),
    (
        "6. Création d'un dépôt GitHub",
        "Paramétrer, confirmer, créer",
        [
            ("bullet", "Renseigner le propriétaire ou laisser vide pour le compte authentifié."),
            ("bullet", "Saisir un nom GitHub valide, une description et choisir privé ou public."),
            ("bullet", "Enregistrer les paramètres, puis sélectionner Créer le dépôt."),
            ("bullet", "Vérifier le nom et la visibilité dans la confirmation avant d'accepter."),
            ("body", "HDP interroge d'abord /user pour identifier le compte. Il appelle ensuite POST /user/repos ou POST /orgs/{org}/repos avec auto_init=true. Une URL déjà associée bloque une seconde création depuis le même projet."),
            ("body", "Le dépôt doit rester privé tant qu'aucune licence et aucune politique de publication n'ont été approuvées."),
        ],
    ),
    (
        "7. Jeton et permissions GitHub",
        "Réduire l'autorité accordée",
        [
            ("body", "Utilisez un jeton finement limité au compte ou à l'organisation nécessaire. GitHub détermine les permissions exactes selon le type de jeton et la visibilité du dépôt."),
            ("bullet", "Préférer la visibilité privée et un jeton à durée de vie limitée."),
            ("bullet", "Ne jamais coller le jeton dans la description, un script, un journal ou un ticket."),
            ("bullet", "Une organisation peut imposer une approbation, un SSO ou interdire la création."),
            ("bullet", "En cas de réponse 401/403, vérifier l'expiration, le propriétaire et les permissions ; ne pas augmenter les droits sans nécessité."),
            ("body", "La création d'un dépôt est un effet externe irréversible par HDP : l'application ne propose pas de suppression distante."),
        ],
    ),
    (
        "8. Profil géographique officiel",
        "ONU M49 et COD-AB OCHA/HDX",
        [
            ("body", "L'utilisateur choisit un élément hiérarchique ONU M49. HDP développe un groupement vers ses pays ou zones descendants, puis cherche les identifiants canoniques cod-ab-* portant un niveau COD officiel."),
            ("bullet", "La saisie libre d'un identifiant HDX est supprimée de ce module."),
            ("bullet", "Chaque jeu doit avoir l'identifiant exact cod-ab-<iso3>, un niveau cod-enhanced ou cod-standard et un unique groupe ISO3 M49 concordant."),
            ("bullet", "Cette identité canonique compense l'absence de dataseries_name dans le JSON CKAN sans élargir l'admissibilité."),
            ("bullet", "Le filtre choisit GeoJSON, GeoPackage, Shapefile ou File Geodatabase à partir du format, du nom et de l'extension."),
            ("body", "La réponse CKAN, la décision de sélection et les absences sont archivées avec une empreinte SHA-256. Les licences et restrictions de chaque fiche restent applicables."),
        ],
    ),
    (
        "9. Nomenclature ONU M49",
        "Périmètre statistique officiel et hiérarchisé",
        [
            ("bullet", "278 entités embarquées : monde, régions, sous-régions, régions intermédiaires, pays ou zones."),
            ("bullet", "248 pays ou zones disposent d'un code ISO3 utilisable pour rapprocher les groupes HDX."),
            ("bullet", "Source d'autorité : Division de statistique des Nations Unies, norme M49."),
            ("bullet", "Instantané du 7 août 2026 ; intermédiaire un-m49 2.2.0 sous licence MIT."),
            ("body", "Les groupements M49 sont destinés aux statistiques et n'impliquent aucune position politique de HDP. Ils définissent un filtre de catalogue, sans transformer les géométries."),
        ],
    ),
    (
        "10. Synchronisation géographique",
        "Manuelle ou automatique et persistante",
        [
            ("body", "Synchroniser maintenant enregistre le périmètre M49, interroge le catalogue COD-AB officiel puis lance les téléchargements. Le mode automatique rend le profil immédiatement éligible."),
            ("bullet", "Intervalle accepté : 60 à 43 200 minutes."),
            ("bullet", "La prochaine échéance est avancée avant l'appel distant pour éviter une boucle agressive."),
            ("bullet", "last_status, last_error, last_sync_at et last_acquisition_id restent en base."),
            ("bullet", "Un profil modifié efface ces références obsolètes et passe à sync_required avant le prochain appel."),
            ("bullet", "Les statuts distinguent jeu officiel absent, format absent, échec et résultat partiel."),
            ("bullet", "La politique enhanced_only refuse tout repli ; enhanced_preferred autorise un cod-standard officiel."),
            ("body", "Un échec distant n'arrête pas le planificateur global ; l'erreur bornée reste visible dans le projet."),
        ],
    ),
    (
        "11. Téléchargement sécurisé",
        "Même pipeline pour les ressources géographiques",
        [
            ("bullet", "HTTP et HTTPS seulement ; aucune URL avec identifiants intégrés."),
            ("bullet", "Résolution DNS avant chaque adresse et refus des destinations privées, locales, réservées ou non globales."),
            ("bullet", "Maximum six redirections, toutes revalidées."),
            ("bullet", "Taille contrôlée par Content-Length puis octet par octet pendant le flux."),
            ("bullet", "Un fichier déjà complet ne consomme pas le quota ; les ressources excédentaires sont reportées."),
            ("bullet", "Écriture .part, hachage SHA-256, puis renommage atomique après réussite."),
            ("body", "Ces contrôles réduisent les risques d'épuisement de stockage et de SSRF, mais ne remplacent ni une analyse antivirus, ni une isolation réseau, ni la validation métier des données."),
        ],
    ),
    (
        "12. Données locales",
        "Inventaire, intégrité et suppression contrôlée",
        [
            ("body", "La rubrique Données locales affiche le nombre de ressources, la taille totale, les réussites et les erreurs du projet actif."),
            ("bullet", "Télécharger remet le fichier local au navigateur."),
            ("bullet", "Vérifier SHA-256 recalcule l'empreinte en flux et la compare à la valeur d'acquisition."),
            ("bullet", "Supprimer localement demande confirmation, efface le fichier et marque la ligne deleted."),
            ("body", "L'acquisition et sa provenance restent conservées après suppression. Pour un COD-AB, la ligne conserve M49, ISO3, niveau COD, éditeur, licence et date des métadonnées HDX."),
        ],
    ),
    (
        "13. Planifications générales",
        "Acquisitions ReliefWeb ou HDX",
        [
            ("body", "Les planifications 2.0 restent disponibles en parallèle du profil géographique. Elles mémorisent source, requête, limite de résultats, intervalle et option de téléchargement."),
            ("bullet", "Intervalle minimal : 15 minutes ; maximum : 30 jours."),
            ("bullet", "Exécuter maintenant attend le résultat et crée une entrée d'historique."),
            ("bullet", "Suspendre conserve la définition ; archiver la retire des listes actives."),
            ("body", "ReliefWeb exige un appname pré-approuvé. Une cadence techniquement autorisée peut rester inadaptée aux quotas ou à l'ampleur de la recherche."),
        ],
    ),
    (
        "14. Migration et conservation",
        "Mise à niveau idempotente depuis 1.5, 2.0 ou 2.3.0",
        [
            ("bullet", "Les acquisitions sans projet rejoignent le Projet par défaut."),
            ("bullet", "Les tables project_github_settings et project_geodata_settings sont créées et initialisées pour chaque projet."),
            ("bullet", "La synchronisation géographique reste désactivée par défaut après migration."),
            ("bullet", "Une ancienne portée monde devient M49 001 ; toute portée plus étroite exige un choix M49 explicite."),
            ("bullet", "Le volume PostgreSQL, data, .env et les images Docker déjà présentes sont conservés."),
            ("body", "Avant toute mise à niveau importante, sauvegardez .env, data et le volume PostgreSQL. N'utilisez pas docker compose down -v, Clean/Purge data ou Reset to factory defaults si les données doivent être conservées."),
        ],
    ),
    (
        "15. Modèle de sécurité",
        "Garanties présentes et limites assumées",
        [
            ("bullet", "Application locale mono-utilisateur, sans authentification applicative ni TLS local."),
            ("bullet", "Secrets hors base projet, scripts jamais exécutés, suppressions confirmées."),
            ("bullet", "Dépôt GitHub privé par défaut ; aucun téléversement implicite."),
            ("bullet", "Données et secrets en clair sur le disque du compte Windows."),
            ("body", "Ne stockez pas de données personnelles, confidentielles ou à protection renforcée sans analyse adaptée. Les mots-clés sont transmis à la source choisie et les créations GitHub agissent sur le compte associé au jeton."),
        ],
    ),
    (
        "16. API locale",
        "Principales routes 2.3.2",
        [
            ("bullet", "GET/PUT /api/projects/{id}/github ; POST .../github/repository."),
            ("bullet", "GET/PUT /api/projects/{id}/geodata ; POST .../geodata/sync."),
            ("bullet", "GET /api/un-m49/entities pour le catalogue hiérarchique et sa source."),
            ("bullet", "GET /api/search, /api/resources, /api/acquisitions et routes de planification héritées."),
            ("body", "La documentation Swagger locale est disponible sur /docs. Certaines routes GET/POST créent des acquisitions ou des fichiers ; elles ne doivent pas être considérées comme purement consultatives."),
            ("body", "La réponse GitHub expose token_configured comme booléen, jamais la valeur du secret."),
        ],
    ),
    (
        "17. Diagnostic",
        "Collecte bornée et non sensible",
        [
            ("body", "HDP_Diagnostic_v2.3.2.cmd crée HDP_Debug_v2.3.2_*.log sur le Bureau et limite chaque commande externe à 15 secondes."),
            ("bullet", "Le diagnostic relève Windows, espace disque, outils, WSL, Docker, ports et journaux applicatifs."),
            ("bullet", "Dans .env, seule la ligne HDP_PORT est copiée."),
            ("bullet", "POSTGRES_PASSWORD, RELIEFWEB_APPNAME et GITHUB_TOKEN sont exclus."),
            ("body", "Relisez néanmoins le journal avant partage : il peut contenir un nom d'utilisateur, un nom de machine, des chemins ou des métadonnées Docker."),
        ],
    ),
    (
        "18. Validation de la remise",
        "Contrôles exécutables sans Docker",
        [
            ("bullet", "Compilation Python et 24 tests unitaires de sécurité, planification, M49 et sélection COD officielle."),
            ("bullet", "Validation syntaxique JavaScript de l'interface."),
            ("bullet", "Compilation x86_64-windows-gnu et contrôle du format PE32+ GUI."),
            ("bullet", "Reconstruction octet pour octet de tous les fichiers du payload embarqué."),
            ("bullet", "Test d'intégrité des trois ZIP et recalcul des empreintes SHA-256."),
            ("body", "La migration PostgreSQL/PostGIS et le parcours navigateur complet exigent Docker ; ils doivent être rejoués sur la machine Windows de recette lorsque Docker n'est pas disponible dans l'environnement de construction."),
        ],
    ),
    (
        "19. Livrables",
        "Contenu du dossier dist/v2.3.2",
        [
            ("bullet", "HumanitarianDataPlatform_Setup_Native_GUI_v2.3.2.exe et son empreinte."),
            ("bullet", "HumanitarianDataPlatform_Windows_v2.3.2.zip pour l'utilisateur Windows."),
            ("bullet", "HumanitarianDataPlatform_Source_v2.3.2.zip pour la reconstruction."),
            ("bullet", "HumanitarianDataPlatform_Archive_complete_v2.3.2.zip pour la remise complète."),
            ("bullet", "Notice, README court, diagnostic, manifeste, prompt de reprise et SHA256SUMS.txt."),
            ("body", "Les livrables 2.3.0, 2.0 et 1.5 historiques restent dans leurs dossiers dédiés et ne sont pas modifiés."),
        ],
    ),
    (
        "20. Checklist de recette",
        "À exécuter sur Windows avec Docker",
        [
            ("bullet", "Mettre à niveau une copie d'installation et vérifier la conservation de .env, data et PostgreSQL."),
            ("bullet", "Créer un projet, enregistrer un dépôt privé de test, confirmer sa création puis vérifier son URL."),
            ("bullet", "Choisir un pays M49, tester enhanced_only puis enhanced_preferred et vérifier les jeux retenus."),
            ("bullet", "Tester un périmètre régional, le report au-delà du quota, la provenance et le SHA-256 local."),
            ("bullet", "Archiver un projet et confirmer la désactivation des automatisations sans perte de fichiers."),
            ("body", "Supprimer manuellement le dépôt GitHub de test après la recette si sa conservation n'est pas souhaitée ; HDP ne supprime aucun dépôt distant."),
        ],
    ),
    (
        "21. Références et assistance",
        "Sources officielles et points de contrôle",
        [
            ("bullet", "GitHub REST API — Repositories : docs.github.com/en/rest/repos/repos"),
            ("bullet", "ONU M49 : unstats.un.org/unsd/methodology/m49/overview/"),
            ("bullet", "OCHA COD-AB : knowledge.base.unocha.org — Administrative Boundaries COD-AB"),
            ("bullet", "CKAN Action API : docs.ckan.org/en/latest/api"),
            ("bullet", "ReliefWeb API V2 : apidoc.reliefweb.int"),
            ("body", "Commencez le dépannage par HDP_Diagnostic_v2.3.2.cmd, puis fournissez le journal relu, le statut Docker, la version Windows et l'étape exacte en échec. Ne communiquez jamais .env ni un jeton GitHub."),
            ("body", "Fin de la notice · Humanitarian Data Platform 2.3.2"),
        ],
    ),
]


def header(c: canvas.Canvas, page_number: int, title: str, subtitle: str) -> float:
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 47 * mm, PAGE_W, 47 * mm, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, PAGE_H - 47 * mm, 7 * mm, 47 * mm, fill=1, stroke=0)
    c.setFont(FONT_BOLD, 18 if page_number else 23)
    c.setFillColor(colors.white)
    c.drawString(18 * mm, PAGE_H - 24 * mm, title)
    c.setFont(FONT, 9.4)
    c.setFillColor(colors.HexColor("#BBD5E8"))
    c.drawString(18 * mm, PAGE_H - 33 * mm, subtitle)
    c.setFont(FONT_BOLD, 8)
    c.setFillColor(CYAN)
    c.drawRightString(PAGE_W - 16 * mm, PAGE_H - 13 * mm, "HDP 2.3.2")
    return PAGE_H - 59 * mm


def footer(c: canvas.Canvas, page_number: int) -> None:
    c.setStrokeColor(LINE)
    c.line(16 * mm, 16 * mm, PAGE_W - 16 * mm, 16 * mm)
    c.setFont(FONT, 7.5)
    c.setFillColor(MUTED)
    c.drawString(16 * mm, 10 * mm, "Humanitarian Data Platform 2.3.2 · notice détaillée")
    c.drawRightString(PAGE_W - 16 * mm, 10 * mm, f"{page_number + 1} / {len(PAGES)}")


def draw_flowable(c: canvas.Canvas, flowable, y: float) -> float:
    width = PAGE_W - 36 * mm
    _, height = flowable.wrap(width, PAGE_H)
    if y - height < 21 * mm:
        raise RuntimeError("Contenu trop long pour une page")
    flowable.drawOn(c, 18 * mm, y - height)
    return y - height


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=A4, pageCompression=1)
    c.setTitle("Notice détaillée Humanitarian Data Platform 2.3.2")
    c.setAuthor("Humanitarian Data Platform")
    c.setSubject("Installation, GitHub, ONU M49, COD-AB officiel et sécurité")
    for page_number, (title, subtitle, blocks) in enumerate(PAGES):
        y = header(c, page_number, title, subtitle)
        if page_number == 0:
            c.setFillColor(PALE)
            c.roundRect(18 * mm, y - 28 * mm, PAGE_W - 36 * mm, 24 * mm, 3 * mm, fill=1, stroke=0)
            c.setFont(FONT_BOLD, 11)
            c.setFillColor(BLUE)
            c.drawString(25 * mm, y - 14 * mm, "VERSION DE REMISE · 2.3.2")
            c.setFont(FONT, 8.5)
            c.setFillColor(MUTED)
            c.drawString(25 * mm, y - 21 * mm, "Dépôt GitHub par projet · ONU M49 · COD-AB officiels OCHA/HDX")
            y -= 35 * mm
        for kind, text in blocks:
            style = {"lead": LEAD, "h2": H2, "body": BODY, "bullet": BULLET, "small": SMALL}[kind]
            paragraph = Paragraph(text, style, bulletText="•" if kind == "bullet" else None)
            y = draw_flowable(c, paragraph, y)
        footer(c, page_number)
        c.showPage()
    c.save()


if __name__ == "__main__":
    build()
    print(OUTPUT)
