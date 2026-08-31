# dev_connecteurs — procédure de développement et qualification des connecteurs HDP

Version: 1.0 — HDP V7

## Mission
Développer ou refondre un connecteur HDP à partir de preuves documentaires vérifiables, sans masquer les capacités natives du fournisseur et sans inventer de nomenclature, d'identifiant, d'endpoint, de paramètre ou de résultat.

## Règles non négociables
1. Le code et les tests observés priment sur les intentions historiques.
2. Un test non exécuté n'est jamais PASS.
3. HTTP 4xx/5xx, timeout, erreur de mapping, authentification ou changement de contrat ne signifient jamais « aucune donnée ».
4. Une recherche bornée, échantillonnée, partielle ou post-filtrée ne peut produire `empty_valid` sans preuve suffisante.
5. Toute traduction géographique ou sémantique doit être documentée et vérifiée. Ne jamais deviner ISO3, M49, identifiant fournisseur ou code agrégé.
6. Conserver la requête native, la réponse native ou sa référence, la normalisation, la provenance, la version du contrat et les limites de l'exécution.
7. Séparer tests déterministes et tests live fournisseur.

## Phase A — recueil documentaire complet
Recueillir prioritairement la documentation officielle : portail, documentation API, OpenAPI/Swagger/SDMX/CKAN/OData, endpoints, méthodes HTTP, authentification, limites, pagination, filtres, tris, facettes, formats, erreurs, changelog, licences et conditions. Recueillir les nomenclatures officielles : pays, territoires, régions, agrégats, indicateurs, thèmes, catégories, organisations, types de contenu, unités, fréquences et vocabulaires contrôlés. Identifier les sources annexes nécessaires à la résolution ou validation des identifiants.

Produire une matrice : SOURCE → ENDPOINT → OPÉRATION → PARAMÈTRE → TYPE → CARDINALITÉ → VALEURS/CODELIST → OBLIGATOIRE → ENTRÉE/SORTIE → SÉMANTIQUE → COMPOSANT UI → PREUVE DOCUMENTAIRE → STATUT HDP.

## Phase B — architecture
Comparer le nouveau fournisseur aux patterns qualifiés ReliefWeb, HDX et World Bank sans copier aveuglément leurs sémantiques. Créer un package fournisseur dédié avec au minimum un descripteur de capacités et un service de référence. Quand une API native spécialisée existe dans HDP, le routeur sémantique doit déléguer à ce service au lieu de maintenir une seconde implémentation.

Pipeline obligatoire : intention utilisateur → concept canonique HDP → nomenclature → capacité fournisseur → traduction vérifiée → valeur fournisseur → paramètre natif → requête native → réponse → normalisation → provenance → UI/export/clients.

## Phase C — exposition UI
Chaque paramètre qualifié doit être exposable selon son type : booléen=case à cocher ; enum=liste ; multi-enum=multi-sélection ; nombre=champ numérique ; intervalle=bornes ; date=calendrier ; période=intervalle temporel ; texte=champ ; mots-clés=recherche ; géographie=nomenclature/liste/carte ; structure complexe=éditeur spécialisé. Les modes Simple/Avancé/Expert peuvent réduire la densité visuelle mais ne doivent pas supprimer l'accès Expert aux capacités qualifiées.

## Phase D — clients reproductibles
Ajouter les méthodes spécialisées Python et R correspondant aux opérations qualifiées. Ajouter exemples et vignette reproductible ; générer HTML/PDF lorsque l'environnement de build le permet. Les scripts ne doivent contenir aucun secret.

## Phase E — normalisation et nomenclatures dynamiques
Normaliser séparément observations, catalogues et métadonnées lorsque leurs contrats diffèrent. Les listes statiques ne sont qu'un garde-fou transitoire : lorsque le fournisseur publie un catalogue officiel exploitable, le charger dans le cache de vocabulaire versionné HDP avec date de vérification, source, hash/version et distinction pays/territoire/agrégat.

## Phase F — qualification par fonctionnalité
Établir la liste des fonctionnalités déclarées. Pour CHAQUE fonctionnalité, exécuter 10 cycles complets : test → observation → diagnostic → audit documentaire si anomalie → correction → nouveau test → audit de non-régression. Conserver le résultat de chaque cycle. Ne pas compter dix fois le même résultat sans réexécution réelle.

Statuts : PASS / FAIL / BLOCKED / NOT TESTED. Une fonctionnalité ne devient qualifiée que si les dix cycles requis passent ou si le protocole de release approuvé définit explicitement un autre seuil.

## Phase G — tests live
Après les tests déterministes, exécuter des sentinelles non destructives contre le fournisseur : cas nominal, géographie connue, période connue, résultat connu/non vide si possible, pagination et erreur contrôlée. Enregistrer HTTP status, URL/requête native expurgée, date, version de contrat et résultat. Une indisponibilité fournisseur est BLOCKED/PROVIDER_ERROR, jamais un faux zéro.

## Phase H — intégration HDP complète
Tester routeur sémantique, API native, UI, projets/configuration, provenance, jobs, export, clients Python/R, migrations/cache si concerné, sécurité, tests de régression des autres connecteurs, build Windows et workflow V7. Exécuter ensuite 10 cycles d'architecture complète avec les connecteurs nouvellement intégrés et les invariants P0.

## Phase I — documentation et log
Créer dans `docs/versions/<version>/<connecteur>/` : audit API+nomenclatures, architecture, matrice fonctionnelle, protocole, résultats des cycles, qualification live, évaluation métier et rapport final. Maintenir un journal chronologique détaillé dans le dépôt avec commits, défauts, décisions et preuves.

## Phase J — évaluation métier
Noter au minimum : pertinence humanitaire, santé publique/épidémiologie, granularité spatiale, profondeur temporelle, fraîcheur, métadonnées, comparabilité internationale, reproductibilité/provenance, robustesse opérationnelle, contraintes d'usage. Distinguer explicitement surveillance temps réel, données contextuelles, données analytiques et données de référence.

## Critères de sortie
Un connecteur n'est `IMPLÉMENTÉ ET QUALIFIÉ` que si son implémentation de référence est unique, ses paramètres qualifiés sont exposés, les nomenclatures ne sont pas devinées, les clients et la provenance sont cohérents, les tests déterministes requis passent, les tests live requis passent ou sont explicitement BLOCKED sans masquer le blocage, et la régression HDP complète est verte. La promotion release reste distincte de la qualification pour test utilisateur.
