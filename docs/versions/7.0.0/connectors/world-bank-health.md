# HDP V7 — Connecteur World Bank Health / WDI

## 1. Objet

Le connecteur `world-bank-health` fournit une intégration spécialisée de la World Bank Indicators API v2. Il est conçu comme connecteur de référence pour HDP V7 : contrat fournisseur documenté, validation typée, génération de requête native, normalisation, provenance, configuration par projet, interface native et interface vers le routeur sémantique canonique.

Le connecteur ne doit jamais confondre documentation fournisseur et qualification HDP. Une capacité peut être documentée par la Banque mondiale sans être implémentée ni qualifiée dans HDP.

## 2. Sources officielles

Documentation officielle utilisée :

- About the Indicators API Documentation — https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation
- API Basic Call Structures — https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures
- Country API Queries — https://datahelpdesk.worldbank.org/knowledgebase/articles/898590-country-api-queries
- Indicator API Queries — https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries
- Aggregate API Queries — https://datahelpdesk.worldbank.org/knowledgebase/articles/898614-aggregate-api-queries
- Topic API Queries — https://datahelpdesk.worldbank.org/knowledgebase/articles/898611-topic-api-queries
- Metadata API Queries — https://datahelpdesk.worldbank.org/knowledgebase/articles/1886695-metadata-api-queries
- New Features and Enhancements in the V2 API — https://datahelpdesk.worldbank.org/knowledgebase/articles/1886674-new-features-and-enhancements-in-the-v2-api

La V2 ne nécessite pas de clé API pour l'accès public. Le format fournisseur par défaut est XML ; le chemin de normalisation HDP V7 est qualifié pour JSON.

## 3. Schéma de développement

Pipeline de référence :

`USER INTENT → HDP CANONICAL CONCEPT → NOMENCLATURE → PROVIDER CAPABILITY → VERIFIED TRANSLATION → WORLD BANK VALUE → NATIVE PARAMETER → NATIVE REQUEST → RESPONSE → NORMALIZATION → PROVENANCE → UI/EXPORT`

Fichiers de référence :

- `source/payload/api/app/providers/world_bank_health/descriptor.py` : identité, opérations, capacités et configuration.
- `source/payload/api/app/providers/world_bank_health/parameters.py` : documentation paramétrique et correspondance sémantique.
- `source/payload/api/app/providers/world_bank_health/service.py` : construction des requêtes, HTTP, catalogues, géographie, normalisation, exécution sémantique.
- `source/payload/api/app/providers/world_bank_health/vocabularies.py` : vocabulaire géographique versionné issu du fournisseur.
- `source/payload/api/app/providers/world_bank_health/api.py` : API spécialisée et interface native.
- `source/payload/api/app/providers/world_bank_health/semantic_interface.py` : interface fournisseur vers le routeur sémantique canonique.
- `source/payload/api/app/semantic_provider_execution.py` : délégation de l'exécution sémantique au `WorldBankHealthService`.
- `source/payload/api/app/v6_semantic_api.py` : routeur sémantique canonique HDP V7, nom conservé pour compatibilité.

## 4. Opérations spécialisées HDP

| Opération HDP | Endpoint HDP | Fonction fournisseur |
|---|---|---|
| descripteur | `GET /api/providers/world-bank-health/descriptor` | contrat HDP |
| paramètres documentés | `GET /api/providers/world-bank-health/parameters` | matrice fournisseur/HDP |
| configuration effective | `GET /api/providers/world-bank-health/configuration/effective` | configuration globale + projet |
| observations | `POST /api/providers/world-bank-health/observations` | country/indicator observations |
| recherche metadata | `POST /api/providers/world-bank-health/metadata` | Metadata API search |
| indicateurs | `GET /api/providers/world-bank-health/indicators` | indicator catalogue |
| pays/économies | `GET /api/providers/world-bank-health/countries` | country catalogue |
| topics | `GET /api/providers/world-bank-health/topics` | topic catalogue |
| sources | `GET /api/providers/world-bank-health/sources` | source catalogue |
| metadata indicateur | `GET /api/providers/world-bank-health/indicator/{indicator}/metadata` | indicator metadata |
| vocabulaire géographique | `GET /api/providers/world-bank-health/geography-vocabulary` | provider country catalogue |
| contrat sémantique | `GET /api/providers/world-bank-health/semantic-contract` | mapping vers routeur HDP |
| plan sémantique WB | `POST /api/providers/world-bank-health/semantic/plan` | routeur canonique, source fixée WB |
| recherche sémantique WB | `POST /api/providers/world-bank-health/semantic/search` | routeur canonique, source fixée WB |
| interface native | `GET /api/providers/world-bank-health/ui` | contrôles natifs |
| interface sémantique | `GET /api/providers/world-bank-health/semantic-ui` | contrôles canoniques |

## 5. Paramètres natifs implémentés et qualifiés

| Paramètre | Placement | Type HDP | Défaut | Sémantique | Interaction | Exposition |
|---|---|---|---|---|---|---|
| `country` | path | string/list | `all` | pays/économie ; plusieurs codes avec `;` | géographie souveraine vérifiée ISO3 | UI/API/projet |
| `indicator` | path | string/list | requis observations | code de série/indicateur | plusieurs indicateurs avec `;` | UI/API/projet |
| `source` | query/path | integer | `2` | source World Bank ; 2 = WDI | requis pour multi-indicateur selon documentation | UI/API/projet |
| `date` | query | YYYY ou YYYY:YYYY | vide | période d'observation | le fournisseur accepte aussi mois/trimestre ; non qualifiés par le modèle actuel | UI/API/projet |
| `page` | query | integer | 1 | pagination | >=1 | UI/API/projet |
| `per_page` | query | integer | 50 observations | taille de page | défaut fournisseur documenté 50 | UI/API/projet |
| `mrv` | query | integer nullable | null | N valeurs les plus récentes | fonctionne avec gapfill/frequency | UI/API/projet |
| `mrnev` | query | integer nullable | null | N valeurs non vides les plus récentes | indépendant de `mrv` dans le modèle | UI/API/projet |
| `gapfill` | query | bool → Y | false | recherche d'une période disponible antérieure | fournisseur : avec MRV | UI/API/projet |
| `frequency` | query | enum | vide | Y/Q/M | fournisseur : avec MRV | UI/API/projet |
| `footnote` | query | bool → y | false | ajoute les notes d'observation | enrichissement de sortie | UI/API/projet |
| `format` | query | enum | json | format de réponse | JSON seul qualifié dans HDP | UI/API/projet |
| `language` | path | enum HDP | en | préfixe localisé | sous-ensemble qualifié HDP : en/fr/es/ar/zh | UI/API/projet |
| `search` | path Metadata API | string | requis | recherche metadata par mots-clés | exposé comme `query` dans l'API spécialisée metadata | UI/API |

Le contrat machine lisible complet est dans `parameters.py` et disponible par `/parameters`.

## 6. Paramètres fournisseur documentés mais non totalement implémentés

| Paramètre/capacité | Documentation | Statut HDP |
|---|---|---|
| `topic` | filtrage d'indicateurs par topic | SPÉCIFIÉ / PLANIFIÉ |
| `incomeLevel` | filtre du catalogue pays | SPÉCIFIÉ / PLANIFIÉ |
| `region` | filtre du catalogue pays | SPÉCIFIÉ / PLANIFIÉ |
| `lendingType` | filtre du catalogue pays | SPÉCIFIÉ / PLANIFIÉ |
| `downloadformat` | téléchargements CSV/Excel selon opération | SPÉCIFIÉ / PLANIFIÉ |
| `dataformat=table/list` | mise en forme des téléchargements | SPÉCIFIÉ / PLANIFIÉ |
| concepts Metadata API | dimensions metadata | PARTIELLEMENT IMPLÉMENTÉ |
| metatypes Metadata API | types metadata | PARTIELLEMENT IMPLÉMENTÉ |
| XML | format fournisseur par défaut | DOCUMENTÉ, NON QUALIFIÉ par le chemin de normalisation V7 |
| périodes mensuelles/trimestrielles via `date` | supportées par la documentation | DOCUMENTÉES, NON QUALIFIÉES par le modèle `WorldBankObservationRequest` actuel |

Ces capacités ne doivent pas apparaître comme `IMPLÉMENTÉ ET QUALIFIÉ` avant ajout du modèle, de l'UI, de la sérialisation, des tests et de preuves live.

## 7. Interface vers le routeur sémantique

L'interface fournisseur ne crée pas un second moteur sémantique. Elle construit un `SemanticSearchRequest` canonique avec la source fixée à `world-bank-health`, puis appelle le même routeur que l'interface multi-sources.

Contrat canonique :

- `project_id` : contexte projet HDP, jamais envoyé à World Bank ; UUID obligatoire.
- `query` : thème/mots-clés ; sert à découvrir des indicateurs, jamais à inventer un code.
- `location` : texte géographique utilisateur ; résolution HDP puis vérification catalogue World Bank.
- `date_from`, `date_to` : intervalle ISO HDP converti vers la représentation fournisseur qualifiée.
- `result_limit` : borne de restitution ; ne constitue jamais une preuve d'exhaustivité.

Routes :

- plan canonique : `/api/semantic/plan`
- exécution canonique : `/api/semantic/search`
- pont World Bank plan : `/api/providers/world-bank-health/semantic/plan`
- pont World Bank recherche : `/api/providers/world-bank-health/semantic/search`
- interface graphique World Bank sémantique : `/api/providers/world-bank-health/semantic-ui`

## 8. Traductions sémantiques

### Thème → indicateur

`query="malaria"` n'est jamais transformé arbitrairement en `SH.MLR.INCD.P3`. Le service interroge le catalogue d'indicateurs de la source configurée, filtre sur les métadonnées disponibles et sélectionne uniquement des codes démontrés par la réponse fournisseur. Si aucune correspondance vérifiée n'est disponible dans le périmètre borné, le résultat doit rester partiel/bloqué selon le plan et ne pas inventer un code.

### Géographie → country

`location="Rwanda"` suit :

`Rwanda → concept géographique HDP → ISO3 RWA → vérification dans le catalogue World Bank → country/RWA`.

`project_id` reste un UUID HDP et ne peut jamais devenir `Rwanda`, `RWA`, `646` ou un identifiant fournisseur.

Les agrégats World Bank comme `WLD` ou `SSA` ne sont pas assimilés à des pays souverains. Ils nécessitent une sémantique d'agrégat explicite.

### Dates

Le routeur sémantique porte des dates ISO. Le connecteur qualifié actuel les ramène à des années pour la requête d'observation World Bank. Les modes mensuels/trimestriels sont documentés par le fournisseur mais ne doivent pas être déduits sans sélection explicite et tests dédiés.

## 9. Complétude et règle anti-faux-zéro

Une page d'observations vide, un catalogue borné ou une recherche d'indicateurs limitée ne prouve pas l'absence globale de données chez le fournisseur. Les réponses bornées vides sont `partial` tant qu'une preuve exhaustive n'existe pas.

Invariant :

`BOUNDED / SAMPLED / PARTIAL / UNKNOWN != empty_valid`.

## 10. Provenance

Toute exécution doit permettre d'inspecter :

- paramètres HDP reçus ;
- configuration globale/projet utilisée ;
- traduction sémantique ;
- code géographique et code indicateur retenus ;
- méthode et URL natives ;
- query string native ;
- HTTP status lorsque disponible ;
- réponse native ou empreinte ;
- normalisation HDP ;
- complétude ;
- empreinte de requête et provenance du routeur sémantique.

## 11. Tests obligatoires

Le connecteur doit conserver au minimum : validation ISO3, séparation pays/agrégats, vocabulaire dynamique, paramètres avancés, multi-pays, multi-indicateurs, langue, metadata, normalisation, prévisualisation native, configuration par projet, délégation sémantique au service de référence, anti-faux-zéro, absence de contamination `location → project_id`, documentation paramétrique, contrat du pont sémantique et exposition des routes.

Les tests live World Bank restent séparés des tests déterministes. Une erreur réseau ou fournisseur reste une erreur et n'est jamais transformée en absence de données.

## 12. Statut

Le noyau observation/catalogue/metadata actuellement qualifié reste `IMPLÉMENTÉ ET QUALIFIÉ` sur son périmètre testé. La documentation nouvellement consolidée rend explicites les capacités fournisseur non encore implémentées. Le connecteur ne doit donc pas être présenté comme couverture exhaustive de toutes les fonctionnalités possibles de la World Bank Indicators API tant que les capacités marquées planifiées/partielles ne sont pas développées et qualifiées.
