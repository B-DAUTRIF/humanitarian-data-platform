# GDACS — dossier connecteur HDP V7

## A. Audit API et nomenclatures

Sources officielles : Swagger GDACS, quickstart API 2025 et portail GDACS. Périmètre qualifiable de ce lot : recherche non destructive `events/geteventlist/SEARCH` retournant des événements géoréférencés. Paramètres déclarés : `eventlist`, `fromdate`, `todate`, `alertlevel`. Types d'événement contrôlés : EQ, FL, TC, TS, VO, DR, WF. Niveaux : green, orange, red. Les autres opérations Swagger et flux KML restent documentés mais non qualifiés dans ce lot.

## B. Architecture

Package `app/providers/gdacs/`; `GDACS_DESCRIPTOR` décrit le contrat, `GDACSService` construit la requête native et normalise via le parseur HDP existant, `/api/providers/gdacs/*` expose descriptor/configuration/query/UI. Le routeur sémantique délègue au même service.

## C. Matrice fonctionnelle

|Paramètre|Type|Cardinalité|UI|Traduction|
|---|---|---|---|---|
|eventlist|array enum|0..7|Simple|liste → chaîne `;`|
|fromdate|string date|0..1|Simple|date début native|
|todate|string date|0..1|Simple|date fin native|
|alertlevel|array enum|0..3|Avancé|liste → chaîne `;`|

La géographie générique HDP n'est **pas** transformée en filtre pays GDACS : faute de mapping natif vérifié elle reste `BLOCKED_MISSING_MAPPING`.

## D-E. UI, clients, normalisation

UI Simple/Avancé/Expert générée depuis le contrat; requête native et documentation visibles. Clients : `gdacs_query()` Python et `hdp_gdacs_v7()` R. La normalisation conserve les propriétés et ressources d'événement ainsi que la réponse native/provenance.

## F-G. Qualification

Dix cycles déterministes sont exécutés par le gate commun. La sentinelle live interroge une fenêtre récente non destructive. Toute indisponibilité ou erreur de schéma devient `BLOCKED`, jamais un résultat vide valide.

Statut avant inspection du head final : **IMPLÉMENTÉ MAIS NON QUALIFIÉ**.

## H-I. Intégration et traçabilité

Code : `providers/gdacs/{descriptor,service,api}.py`; tests : `test_v7_six_provider_services.py`; audits : `v7_six_connectors_*`. Le filtre thématique générique est explicitement un filtrage HDP après réponse, tandis que dates/types/niveaux sont natifs.

## J. Évaluation métier

GDACS est une source de **contexte événementiel rapide** utile en humanitaire. HDP la traite comme outil analytique et ne doit jamais la présenter comme remplacement d'un canal officiel de sécurité civile ou d'alerte vitale.
