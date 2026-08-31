# HDP V7 — rapport final d'audit systématique paramètre-par-paramètre

## Périmètre

Cette campagne applique `docs/prompts/audit_parametres_connecteurs_v7.md` aux familles ReliefWeb, World Bank Health/WDI et HDX. HDX est séparé en contrats HDX/CKAN `package_search` et HDX HAPI v2 ; COD reste distinct et n'est pas assimilé à CKAN ou HAPI.

Base de campagne : `d0948e8337f4f1bd0dec762f67f8d27a2eb6136a`.

Le protocole audite la chaîne : fournisseur → API → endpoint → opération → paramètre → valeur/type → requête native → réponse → normalisation → interface HDP → test → preuve. Les résultats live sont séparés des résultats déterministes et un blocage fournisseur n'est jamais interprété comme une absence de données.

## Résultats déterministes

Le contrôleur `tools/v7_systematic_parameter_audit.py` a inventorié **82 lignes de paramètres/contrats** et exécuté **34 contrôles indépendants de binding/non-contamination**. Le workflow les a rejoués sur **10 cycles réels**. Les dix cycles ont produit le même verdict :

`PASS_WITH_EXPLICIT_DEBT`

Les régressions connecteurs/routeur sémantique, le test de non-contamination `location=Rwanda` / `project_id`, les dix cycles d'architecture ReliefWeb+World Bank et l'audit release-readiness ont également passé sur le commit de qualification précédent `2798a9b9b15a7f10ee14da35f2459f8f06b4f8c4`.

Le statut `PASS_WITH_EXPLICIT_DEBT` signifie que les invariants testés passent mais que des capacités documentées restent volontairement ou techniquement non exposées/qualifiées. Il ne signifie pas que l'intégralité des API fournisseurs est qualifiée.

## ReliefWeb V2

### Couverture déterministe

Le descripteur/service spécialisé couvre les paramètres natifs de premier niveau et structures qualifiées : `appname`, `query`, `filter`, `facets`, `limit`, `offset`, `sort`, `profile`, `preset`, `fields`, `slim`, `verbose`, ainsi que les neuf types de contenu et la restriction des endpoints item à `fields`/`profile`.

Les bindings spécialisés sont testés indépendamment. Le registre générique reste plus étroit mais le chemin spécialisé constitue la référence fonctionnelle pour ces capacités.

### Live

La campagne live du commit `2798a9b9b15a7f10ee14da35f2459f8f06b4f8c4` a exécuté **28 sondes ReliefWeb** couvrant paramètres, structures récursives/facettes et neuf content types. Toutes ont reçu **HTTP 403** avec le message fournisseur indiquant que `HDP_plateforme` n'est pas un appname approuvé.

Statut : **BLOQUÉ — BLOCKED_PENDING_PROVIDER_ACCEPTANCE_OF_APPNAME**.

Ce 403 n'est jamais converti en résultat vide et ne remet pas en cause les tests déterministes. Il interdit en revanche de déclarer la qualification live paramètre-par-paramètre ReliefWeb complète.

## World Bank Health / WDI

### Couverture déterministe

Le chemin JSON qualifié couvre `source`, `country`, `indicator`, `date`, `page`, `per_page`, `mrv`, `mrnev`, `gapfill`, `frequency`, `footnote`, `format=json`, `language`, ainsi que catalogues indicateurs/pays/topics/sources, métadonnées et métadonnées d'indicateur. Le catalogue géographique distingue pays/territoires et agrégats.

### Live

La campagne corrigée a obtenu **23 PASS** pour World Bank, notamment : `source`, `country`, `indicator`, `date`, `page`, `per_page`, `mrv`, `mrnev`, `gapfill`, `frequency`, `footnote`, `ctrycode`, `scale`, JSON, langue via `/v2/fr/...`, multi-country, multi-indicator, catalogues, métadonnées et recherche de métadonnées.

Statut du chemin JSON testé : **IMPLÉMENTÉ ET QUALIFIÉ sur le périmètre explicitement sondé**.

Capacités documentées mais non qualifiées dans le chemin normalisé HDP : JSONP/`prefix`, JSON-stat, `downloadformat` CSV/XML/Excel, `dataformat=list|table`, SDMX et autres formats annexes. Elles restent visibles comme dette/capacité documentée, jamais comme absence.

## HDX / CKAN package_search

### Couverture HDP

HDP expose actuellement `q` via `query`, `fq`, `sort`, `rows` via `result_limit` et `start`.

### Live fournisseur

La campagne a obtenu **9 PASS** pour CKAN : `q`, `fq`, `sort`, `rows`, `start`, `facet`, `facet.mincount`, `facet.limit`, `facet.field`.

Cela prouve que la forme de ces paramètres est acceptée par le service live testé ; cela ne signifie pas que toutes ces capacités sont déjà exposées dans HDP.

### Dette explicite

Les facettes publiques (`facet`, `facet.mincount`, `facet.limit`, `facet.field`) et options Solr/dismax avancées (`use_default_schema`, `qf`, `wt`, `bf`, `boost`, `tie`, `defType`, `mm`) restent **DOCUMENTÉES MAIS NON EXPOSÉES/QUALIFIÉES DANS L'UI HDP**.

`include_drafts`, `include_deleted`, `include_private` sont **NOT_EXPOSED_BY_DESIGN** dans le connecteur public HDX : ce sont des capacités d'autorisation/visibilité qui ne doivent pas être injectées silencieusement dans une interface de découverte publique.

## HDX HAPI v2

HAPI est un contrat distinct de CKAN. HDP expose actuellement l'endpoint, `location_code`, `admin_level`, `offset`, la limite commune et l'identifiant d'application en configuration. La normalisation qualifiée est JSON.

Le contrat fournisseur documente des filtres dépendants des sous-endpoints, notamment `sector_name`, `admin1_code`, `admin1_name`, `admin2_code`, `org_name`, `age_range_code`, `gender_code`, `resource_hdx_id`, `update_date_min`, `update_date_max`.

Ces paramètres sont classés **ENDPOINT_FILTER_NOT_EXPOSED** tant que leur contrat courant complet n'est pas récupéré/qualifié et que l'UI n'est pas individualisée par sous-endpoint.

La qualification live est **BLOCKED** car `HDX_HAPI_APP_IDENTIFIER` n'est pas disponible dans l'environnement de qualification. Ce blocage ne signifie jamais absence de données.

## Non-contamination des paramètres

Le protocole rend permanent le contrôle suivant : modifier un paramètre `P_i` ne doit modifier aucun paramètre `P_j` sans règle explicite. Le cas de référence est l'incident où la valeur métier `rwanda` pouvait atteindre `project_id`.

La correction V7 impose que le mode Simple utilise un UUID de projet déterministe et que les modes Avancé/Expert valident l'UUID avant sérialisation. Le test `source/tests/test_v7_semantic_ui_project_id.py` est inclus dans le gate de cette campagne.

## CI et sémantique des résultats

Le workflow `HDP V7 systematic parameter audit` exécute : compilation, dix cycles du contrôleur paramètre-par-paramètre, régressions connecteurs/sémantique, dix cycles d'architecture, release-readiness, sondes live séparées, puis build Windows 2025 et vérification MZ/SHA-256.

Le step live est `continue-on-error` afin qu'une indisponibilité ou un refus fournisseur ne supprime pas les preuves déterministes et l'artefact d'audit. **Un workflow global SUCCESS ne doit donc jamais être lu comme “tous les tests live sont PASS”.** Les statuts individuels du fichier `LIVE_PARAMETER_AUDIT.json` font foi pour le live.

## Dette restante

1. ReliefWeb : acceptation/activation live de l'appname `HDP_plateforme` requise avant qualification live complète.
2. HDX HAPI : fournir/configurer `HDX_HAPI_APP_IDENTIFIER`, récupérer le contrat courant des sous-endpoints et qualifier leurs filtres individuellement.
3. HDX/CKAN : décider puis implémenter/qualifier l'exposition des facettes publiques et, si utile, des paramètres Solr avancés ; les options privées/drafts/deleted restent hors scope public sauf décision explicite.
4. World Bank : formats annexes/SDMX/downloads restent documentés mais non qualifiés dans le chemin normalisé.
5. Maintenir la matrice `DOCUMENTATION ↔ DESCRIPTOR ↔ REGISTRY ↔ BACKEND ↔ UI ↔ PYTHON ↔ R ↔ TESTS ↔ DOC` comme gate de toute future modification.

## Verdict

### World Bank Health / WDI — périmètre JSON testé
**IMPLÉMENTÉ ET QUALIFIÉ** sur les paramètres explicitement couverts par les tests déterministes et live.

### HDX / CKAN
**PARTIELLEMENT IMPLÉMENTÉ / QUALIFICATION PARTIELLE** : le cœur `package_search` exposé est qualifié ; plusieurs paramètres publics documentés et live-acceptés restent non exposés dans HDP.

### HDX HAPI v2
**PARTIELLEMENT IMPLÉMENTÉ / BLOQUÉ POUR QUALIFICATION LIVE COMPLÈTE** : contrat commun partiel, filtres d'endpoints non exposés, identifiant applicatif absent dans l'environnement de qualification.

### ReliefWeb V2
**IMPLÉMENTÉ MAIS NON QUALIFIÉ LIVE SUR CETTE CAMPAGNE** : déterministe vert, mais 403 fournisseur pour l'appname.

### Campagne globale paramètre-par-paramètre
**QUALIFICATION PARTIELLE**.

Ce verdict n'abaisse pas artificiellement les sous-ensembles déjà qualifiés : il indique simplement que l'objectif très strict “chaque paramètre de chaque nouveau connecteur est implémenté, exposé et live-qualifié” n'est pas encore atteint. Il interdit de masquer la dette et les blocages derrière un verdict global plus favorable.