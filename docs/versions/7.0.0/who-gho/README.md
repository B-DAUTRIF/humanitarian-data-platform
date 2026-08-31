# WHO GHO — dossier connecteur HDP V7

## A. Audit API et nomenclatures

Documentation officielle : WHO GHO OData API et politique de données OMS. Périmètre spécialisé : `Dimension`, `DIMENSION/{dimension}/DimensionValues`, `Indicator` et `/{indicator}`. L'API OData documente notamment `$filter`; HDP expose des noms sûrs `filter`, `top`, `skip`, `format` puis les traduit en `$filter`, `$top`, `$skip`, `$format`.

Nomenclatures : catalogue `Indicator` pour les codes indicateurs; `Dimension` et `DimensionValues` pour les dimensions. Les nouveaux contrats World Health Data Hub postérieurs au GHO historique ne sont pas assimilés automatiquement à cette API.

## B. Architecture

Package `app/providers/who_gho/`; `WHO_GHO_DESCRIPTOR`, `WHOGHOService`, API/UI spécialisée. Le service construit les chemins OData et conserve la requête native. Le routeur sémantique utilise le même service pour la recherche de catalogue par mots-clés.

La recherche sémantique d'observations avec géographie/période reste explicitement bloquée tant que la surface OMS moderne n'a pas été requalifiée. L'interface Expert garde néanmoins `indicator_data` avec filtre OData explicite.

## C. Matrice fonctionnelle

|Opération|Paramètre HDP|Paramètre natif|Type|UI|
|---|---|---|---|---|
|list_dimensions|top/skip/format|$top/$skip/$format|integer/integer/enum|Avancé/Expert|
|dimension_values|dimension|path|texte|Simple|
|dimension_values|top/skip/format|OData|mixte|Avancé/Expert|
|list_indicators|filter|$filter|texte|Simple|
|list_indicators|top/skip/format|OData|mixte|Avancé/Expert|
|indicator_data|indicator|path|texte|Simple|
|indicator_data|filter|$filter|texte|Simple|
|indicator_data|top/skip/format|OData|mixte|Avancé/Expert|

## D-E. UI, clients et normalisation

UI Simple/Avancé/Expert avec liens OMS et affichage natif. Clients : `who_gho_query()` Python, `hdp_who_gho_v7()` R. Le catalogue indicateurs utilise le normaliseur HDP existant; les autres opérations conservent `_native`.

## F-G. Qualification

Dix cycles déterministes contrôlent les noms OData natifs et le blocage explicite des traductions non requalifiées. La sentinelle live demande un petit catalogue `Indicator`. Une évolution de schéma ou indisponibilité est `BLOCKED`, pas un zéro.

Statut avant inspection du head final : **IMPLÉMENTÉ MAIS NON QUALIFIÉ** pour le périmètre GHO déclaré ; routage sémantique géographie/temps **BLOQUÉ** volontairement.

## H-I. Intégration/traçabilité

Code : `providers/who_gho/`; API montée par `main_v6.py`; semantic dispatch via le service de référence; clients/tests/audits communs au lot. Dette : qualification séparée de la plateforme WHO World Health Data Hub moderne avant toute migration sémantique.

## J. Évaluation métier

WHO GHO est une source **analytique et de référence sanitaire mondiale** essentielle pour indicateurs comparables, métadonnées et séries temporelles. Elle ne doit pas être présentée comme surveillance événementielle temps réel; la version du contrat OMS et la définition de l'indicateur doivent accompagner les résultats.
