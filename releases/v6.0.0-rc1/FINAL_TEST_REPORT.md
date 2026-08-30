# HDP V6.0.0 — Rapport final de tests et évaluation

Date de clôture technique : 2026-08-30

## Décision de qualification

HDP V6.0.0 satisfait toutes les portes automatisables et toutes les recettes hébergées disponibles. Le statut de livraison est **Release Candidate v6.0.0-rc1** tant que les deux portes matérielles obligatoires ci-dessous n'ont pas été exécutées avec succès sur les OS réels correspondants :

- Windows 10 x64, build 19044 ou supérieur et inférieur à 22000 : **EN ATTENTE DE RUNNER SELF-HOSTED RÉEL** ;
- Windows 11 x64, build 22000 ou supérieur : **EN ATTENTE DE RUNNER SELF-HOSTED RÉEL**.

Windows Server 2025 est utilisé comme plateforme CI complémentaire et ne remplace pas ces deux preuves.

## Référentiel fonctionnel

La matrice V6 comporte désormais **42 portes**. Le gate `tools/v6_use_case_gate.py` relie chacune de ces 42 portes à au moins une preuve exécutable, regroupée dans 11 cas d'usage. Sur le dernier HEAD hébergé qualifié, le gate a produit : `features_expected=42`, `features_covered=42`, `missing_features=[]`, `missing_evidence_paths=[]`.

### UC01 — Sources et recherche

Couvre registre des 10 sources, inventaire, contrôles de paramètres, câblage des paramètres, recherche fédérée et filtres épidémiologiques. Preuves : registre source, recherche fédérée, cas épidémiologiste, audit inventaire et parcours navigateur.

### UC02 — Géodonnées et données locales

Couvre COD/M49, CARTE, GeoJSON, acquisition/téléchargement contrôlé, upload local, intégrité et provenance. Le navigateur vérifie la vue CARTE et les API de couches ; le parcours épidémiologique produit un GeoJSON avec provenance ; l'upload est relu octet pour octet et contrôlé par SHA-256.

### UC03 — Projets et GitHub

Couvre CRUD projets, isolation des préférences/ressources/configurations et contrats d'association/synchronisation GitHub. Le navigateur crée deux projets, modifie les préférences, contrôle l'isolation, puis archive/supprime les projets de recette.

### UC04 — Clients scientifiques, scripts et notebooks

Couvre client Python, client R, scripts, notebooks et traitements. Le client R est construit et installé dans une bibliothèque utilisateur temporaire non privilégiée et ses 59 assertions passent. Le client Python est compilé/installé et ses tests passent. Les vues Scripts et Notebooks sont parcourues en navigateur réel et les contrats de traitement sont couverts par les tests Python.

### UC05 — Épidémiologie et surveillance

Couvre séries temporelles, taux/incidence, rafraîchissement/dédoublonnage, règles/signaux/actions et timeline. Scénario de référence : choléra au Mozambique, mars 2026. Résultats de référence vérifiés : 25 cas -> 1,25/100 000 ; rafraîchissement -> 120 cas -> 6,0/100 000 ; seuil > 5/100 000 -> exactement une alerte ; 4 observations dans le GeoJSON final.

### UC06 — Sécurité, sauvegarde et SQL

Couvre sauvegarde/restauration PostgreSQL, contrôles d'accès, passkey/contrats de sécurité et SQL read-only. Le navigateur exécute un `SELECT` autorisé puis vérifie qu'une écriture SQL est rejetée. Les tests d'intégration utilisent une vraie instance PostGIS/PostgreSQL 16.

### UC07 — Mail, SPIP et logs

Couvre mail features/ingestion, bridge/plugin SPIP et journalisation. Les API sont présentes dans le parcours navigateur et les contrats négatifs/positifs sont couverts par la suite Python ; l'installateur écrit ses journaux de diagnostic et les contrôles statiques recherchent les fuites de secrets.

### UC08 — Windows, architecture et UI

Couvre EXE x64, installation/mise à niveau/désinstallation, FastAPI/PostGIS/Docker Compose/R, OpenAPI et navigation Simple/Avancé/Expert. Sur Windows Server 2025, le véritable EXE est exécuté via sa GUI : chemin personnalisé, payload, `.env`, module R, sonde HTTP, raccourci Bureau, seconde installation, sauvegarde `.env.backup-before-v6.0.0`, conservation d'une valeur utilisateur et désinstallation avec conservation des données/configurations utilisateur.

### UC09 — Documentation, migration et release

Couvre documentation, archive, migration/upgrade, compatibilité avec l'état précédent et gate de release. Les livrables sont construits avec SHA-256 et le finaliseur refuse l'ancien inventaire obsolète.

### UC10 — Windows 10 x64

Compilation de l'installateur avec `_WIN32_WINNT=0x0A00` et `NTDDI_VERSION=0x0A000000`, vérification PE/imports et recette réelle dédiée. La recette refuse automatiquement Windows 11 et Windows Server. **Porte réelle actuellement queued faute de runner Windows 10 x64 correspondant.**

### UC11 — Windows 11 x64

Le même binaire Windows 10+ est conservé. La recette Windows 11 vérifie explicitement Caption Windows 11, x64 et build >= 22000 avant d'exécuter le parcours installateur complet. **Porte réelle actuellement queued faute de runner Windows 11 x64 correspondant.**

## Résultats quantitatifs

- Tests Python/PostgreSQL : **295/295 PASS**.
- Recette fournisseurs/épidémiologie : **115/115 PASS**.
- Recette épidémiologique de référence : **PASS**, 2 semaines calculées, 1 alerte, 4 enregistrements.
- Client R : **59 PASS, 0 FAIL, 0 WARN, 0 SKIP**.
- Navigateur réel : **19 vues visitées**, parcours métier étendu PASS.
- API critiques navigateur : health, inventaire, projets, backups, catalogue, RSS, timeline : HTTP 200.
- SQL : lecture autorisée, écriture refusée.
- Upload : création, métadonnées, SHA-256 et restitution du fichier vérifiés.
- Inventaire V6 canonique : **1 020 entrées / 10 sources / 196 opérations / 228 supportées / 792 informatives**.
- JavaScript inline : validation PASS.
- Docker Compose : contrat PASS.
- R/plumber et runner Python : images construites PASS.
- Runner C17 : compilation stricte `-Wall -Wextra -Werror` PASS.
- Sécurité statique HDP 6.0.0 : PASS.
- Installateur MSVC PE32+ Windows GUI x64 : PASS.
- Installation/mise à niveau/désinstallation sur runner Windows complémentaire : PASS.
- Compatibilité statique Windows 10/11 : PASS.
- Compatibilité réelle Windows 10 : **QUEUED — infrastructure requise**.
- Compatibilité réelle Windows 11 : **QUEUED — infrastructure requise**.

## Inventaire des sources

Le référentiel V6 est figé à 10 sources : DHS, GDACS, HDX, HDX HAPI, ReliefWeb, UN SDG, UNHCR, UNICEF SDMX, WHO GHO et World Bank Health. L'ancien référentiel erroné 2057/440 a été supprimé du processus de finalisation. Le finaliseur contrôle les valeurs canoniques 1020/10/196/228/792.

## Évaluation du logiciel

### Fonctionnalité métier — 9/10

La plateforme couvre un spectre large et cohérent : recherche multisource, projets, import, géodonnées, provenance, traitements, surveillance, règles/actions, SQL, sauvegarde, RSS/mail/SPIP, scripts/notebooks et clients R/Python. La cohérence entre paramètres HDP et paramètres fournisseurs a été nettement renforcée.

### Reproductibilité scientifique — 9/10

Le scénario épidémiologique de référence calcule des valeurs numériques déterministes, conserve la provenance, produit une série hebdomadaire et une sortie géographique, puis vérifie une alerte. R et Python disposent de clients testés. Le principal axe futur est d'ajouter davantage de jeux de référence métier réels et versionnés.

### Robustesse et qualité du code — 9/10

La non-régression est large : PostgreSQL réel en CI, tests Python, R, navigateur, C17, sécurité, inventaire et installateur. Les tests autrefois ignorés ont été transformés en preuves exécutées. Le gate refuse désormais une fonctionnalité sans chemin de preuve.

### Installation Windows — 8/10 provisoire

Le véritable installateur est construit avec MSVC x64, inspecté, exécuté, mis à niveau puis désinstallé sur Windows Server 2025 ; sa cible SDK minimale est Windows 10. La note reste volontairement provisoire tant que les deux recettes réelles Windows 10 et Windows 11 ne disposent pas de runners physiques.

### Traçabilité et provenance — 9/10

Les datasets et ressources conservent source, URL/paramètres et empreintes ; les uploads sont vérifiés ; l'inventaire documente origine, statut machine et mapping. La distinction entre paramètres fournisseur informatifs et paramètres HDP réellement configurables évite les faux contrôles UI.

### Maturité globale — 8,8/10 en RC

HDP V6 est une RC techniquement très avancée et fortement testée. **Elle ne doit pas être qualifiée de release finale v6.0.0 tant que les recettes Windows 10 et Windows 11 réelles n'ont pas réussi sur le même état source.** Cette réserve n'est pas une anomalie fonctionnelle connue : elle correspond à l'absence d'infrastructure de test physique requise par la politique de release.

## Livrables

La publication RC doit placer dans `releases/v6.0.0-rc1/` :

- `HumanitarianDataPlatform_Setup_Native_GUI_v6.0.0.exe` ;
- son fichier `.sha256` ;
- `HumanitarianDataPlatform_Archive_complete_v6.0.0-rc1.zip` ;
- son fichier `.sha256` ;
- le présent `FINAL_TEST_REPORT.md` ;
- `WINDOWS_STATIC_COMPATIBILITY.json` ;
- un README de statut.

Les mêmes fichiers sont attachés à la prerelease GitHub `v6.0.0-rc1` afin d'être directement téléchargeables.

## Critère de promotion finale

La promotion de `v6.0.0-rc1` vers `v6.0.0` est autorisée seulement si :

1. CI Linux/PostGIS/R/navigateur/épidémiologie verte ;
2. workflow Windows hébergé complémentaire vert ;
3. recette Windows 10 x64 réelle verte ;
4. recette Windows 11 x64 réelle verte ;
5. les quatre preuves concernent le même état source/release ;
6. aucune porte V6-001..V6-042 n'est `A_TESTER`, `PARTIEL` ou `BLOQUE`.

Aucune de ces règles ne peut être contournée par une simple présence de code ou par un test non exécuté.
