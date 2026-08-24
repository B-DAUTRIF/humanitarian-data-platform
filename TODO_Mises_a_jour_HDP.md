# Todo-list des mises à jour — Humanitarian Data Platform

## Programme HDP 6.0.0 — règles, connecteurs et catalogue

> **État au 21 août 2026** — HDP 6.0.0 devient la version de développement.
> La dernière livraison installable qualifiée reste la 5.0.2. La branche
> distante `develop/5.2` demeure la référence historique immédiatement
> antérieure. Aucun EXE, ZIP ou `main` 6.0.0 ne doit être annoncé avant la
> qualification complète.

La notice de référence est conservée dans
[`docs/NOTICE_TECHNIQUE_FONCTIONNELLE_V6.md`](docs/NOTICE_TECHNIQUE_FONCTIONNELLE_V6.md).
Une case n'est cochée que si le code, les migrations, les tests et la preuve de
non-régression correspondants existent.

**Dernier jalon distant validé au 24 août 2026** : le commit
`bda9f2d0f537…` a réussi 257 tests Python sans test ignoré, dont les
restaurations globale, signaux et projet et les sept recettes du travailleur
d'actions sur PostgreSQL 16. La validation Linux et la construction Windows
sont vertes. Le schéma OpenAPI compte 169 routes dont 55 chemins `/api/v6`.
Les lots sauvegardes et travailleur interne sont fermés dans ce périmètre ; ces
preuves ne remplacent pas la recette Windows/Docker du déploiement cible.

### HDP6-001 — Gouvernance et compatibilité

- [x] intégrer toutes les décisions de la notice dans la todo-list versionnée ;
- [x] déclarer `6.0.0-dev` comme version de développement sans renommer les
  artefacts 5.0.2 ;
- [x] conserver les tables, routes et paramètres 5.x pendant les migrations ;
- [x] maintenir `HDP_STATE.json` pour le lot local 1 ;
- [x] réconcilier les preuves locales et distantes du jalon V6 et empêcher une
  nouvelle divergence du nombre de tests et de fichiers Python ;
- [ ] réconcilier README, référence API, architecture et wiki ;
- [ ] n'effectuer aucune publication, fusion ou livraison sans validation
  explicite et preuve de qualification.

### HDP6-010 — Moteur de règles ET/OU versionné

- [x] représenter chaque règle par un arbre JSON immuable de groupes `AND`/`OR`
  et de feuilles typées ;
- [x] valider l'arbre côté serveur avec profondeur, taille et opérateurs bornés ;
- [x] conserver définition, versions, portée globale/projet, empreinte SHA-256,
  auteur logique et date ;
- [x] permettre l'héritage d'une règle globale, la surcharge par projet et la
  proposition explicite d'une nouvelle version sans remplacement automatique ;
- [x] fournir une simulation sans action avec preuve condition par condition ;
- [ ] migrer les règles 5.x plates vers un arbre compatible sans perte.

### HDP6-011 — Corrélations temporelles

- [x] appliquer réellement `lookback_hours` ;
- [x] prendre en charge le nombre d'événements dans une fenêtre ;
- [x] prendre en charge une séquence ordonnée d'événements ;
- [x] prendre en charge l'absence d'un événement attendu ;
- [x] prendre en charge variation et tendance par rapport à une valeur fixe ou
  à une référence glissante ;
- [x] borner fenêtres, volumes d'événements et coût d'évaluation ;
- [x] enregistrer événements examinés, référence, résultat et version de données.

### HDP6-012 — Actions, limites et idempotence

- [x] séparer évaluation, demande d'action et exécution asynchrone ;
- [x] réserver une clé d'idempotence avant tout effet externe ;
- [x] automatiser seulement notifications internes, classements, tâches HDP et
  recherches/actualisations dans les limites configurées ;
- [x] produire les mails et publications SPIP sous forme de brouillons soumis à
  validation ;
- [x] maintenir scripts Python/R et webhooks en validation
  manuelle avec version et empreinte exactes ;
- [x] placer tout dépassement de volume, durée, requêtes ou téléchargement en
  `pending_approval` ;
- [x] conserver l'indisponibilité réelle des runners et de l'egress tant que
  l'infrastructure n'est pas intégrée.
- [x] réclamer les demandes concurrentes avec `FOR UPDATE SKIP LOCKED`, bail,
  reprise des baux expirés, tentatives bornées et temporisation progressive ;
- [x] annuler une demande en attente ou en cours sans effet partiel et réévaluer
  les limites projet dans la transaction qui précède l'effet ;
- [x] produire idempotemment les notifications, classements, tâches et brouillons
  internes, puis mettre en file les recherches et actualisations ;
- [x] réclamer les travaux de données avec bail et `SKIP LOCKED`, conserver un
  résultat par source, reprendre seulement les sources échouées et refuser une
  seconde acquisition persistée pour le même couple travail/source ;
- [ ] exécuter les travaux `automated_data_jobs` avec les connecteurs réels,
  puis qualifier les appels Internet, quotas de source et annulations pendant
  un transfert en cours ;
- [x] exposer dans l'interface le suivi des tentatives, décisions, brouillons et
  travaux de données associés ; les deux recettes PostgreSQL passent à distance.

### HDP6-020 — Inventaire exhaustif des connecteurs

- [ ] inventorier tous les endpoints officiellement documentés de chaque source ;
- [ ] versionner la documentation officielle et la date de vérification ;
- [ ] recenser paramètres de chemin, requête, en-tête et corps, avec types,
  valeurs par défaut, obligations, listes, limites, dépendances, pagination et tri ;
- [ ] recenser tous les champs documentés et observés dans les réponses, y compris
  chemins imbriqués, cardinalité, nullabilité et version d'apparition ;
- [ ] recenser toutes les métadonnées des jeux et fichiers ;
- [ ] recenser méthode, URL, authentification, quotas, formats, délais, cache,
  hôtes autorisés, version et paramètres techniques ;
- [x] distinguer strictement inventaire documentaire et exécution effective.

### HDP6-021 — Activation progressive et socle commun

- [x] gérer les états `inventoried`, `contract_imported`, `adapter_implemented`,
  `tests_validated`, `active_global`, `active_project`, `suspended`, `obsolete` ;
- [x] activer les endpoints progressivement, sans assimiler inventaire et support ;
- [ ] faire atteindre à toutes les sources le socle `discover`, `describe`,
  `search`, `preview`, `acquire`, `refresh`, `provenance` avant les fonctions
  spécialisées ;
- [ ] générer formulaires et contrôles depuis les contrats serveur ;
- [ ] conserver les paramètres historiques lors des évolutions de contrat.

### HDP6-030 — Catalogue central et fidélité des données

- [x] créer le schéma central versionné des versions d'API, endpoints,
  paramètres, champs de réponse, capacités et métadonnées ;
- [x] conserver les métadonnées brutes immuables avant normalisation ;
- [x] exposer l'identifiant interne des métadonnées nécessaire à l'agrégation ;
- [x] ne jamais fabriquer une métadonnée absente : utiliser une valeur
  explicitement indisponible avec niveau de confiance ;
- [x] signaler toute dérive de contrat au lieu de supprimer silencieusement un
  champ nouveau ou modifié ;
- [x] tracer champ brut, champ normalisé, recette, version du connecteur et
  paramètres d'acquisition ;
- [x] corriger la sémantique `ready` des plans d'agrégation en validant réellement
  géographie, unités, clés de jointure, périodes et licences.

### HDP6-031 — Équivalents fonctionnels HDP

- [x] générer à la demande et mettre en cache un équivalent déclaré lorsqu'une
  capacité du socle manque ;
- [ ] paginer une API et produire JSON, Parquet et CSV lorsqu'aucun fichier
  téléchargeable n'existe ;
- [ ] combiner documentation officielle et champs observés lorsqu'aucun schéma
  n'existe, avec provenance et confiance ;
- [ ] produire un aperçu borné et non persistant ;
- [ ] comparer ETag, Last-Modified, empreinte ou contenu lorsqu'aucune fonction de
  mise à jour n'existe ;
- [ ] normaliser les géographies vers M49/ISO et produire GeoJSON/GeoPackage
  lorsque les données le permettent.

### HDP6-040 — Cache, fraîcheur et politique de projet

- [x] construire une clé canonique incluant source, version, endpoint, paramètres,
  format, version du connecteur et version de transformation, sans secret ;
- [x] partager les artefacts publics identiques sans dupliquer les fichiers ;
- [x] revalider avec ETag/Last-Modified, fréquence déclarée, durée par source,
  version technique et forçage utilisateur ;
- [x] écrire temporairement, vérifier taille et empreinte, puis publier atomiquement ;
- [x] appliquer une politique unique à tout le projet ;
- [x] appliquer par défaut `stale_if_error` : actualiser d'abord, puis utiliser
  l'ancienne version uniquement après échec et dans l'ancienneté autorisée ;
- [x] rendre configurables les quatre calculs d'ancienneté maximale : durée fixe,
  multiple de fréquence, fréquence avec plafond projet, décision manuelle ;
- [ ] **arbitrage restant** : choisir le calcul proposé par défaut dans l'interface.

### HDP6-050 — Interface des sources et des règles

- [x] ajouter un bouton **Paramétrages** dans chaque encart de source ;
- [x] conserver les portées globale et projet dans ce sous-menu ;
- [ ] afficher Endpoints, Paramètres d'entrée, Champs de réponse, Métadonnées,
  Technique, Historique et état d'activation ;
- [x] afficher en lecture le fichier de configuration et les liens Portail,
  Documentation et API ;
- [x] présenter listes, cases à cocher et menus pour les valeurs contraintes,
  et champs typés pour les valeurs libres ;
- [ ] fournir un constructeur visuel ET/OU, une formule textuelle, un arbre et une
  simulation avant enregistrement ;
- [ ] limiter l'interface à environ cinq niveaux d'imbrication tout en laissant le
  moteur et le schéma de données gérer les arbres valides plus profonds.

### HDP6-060 — Chronologie, sécurité et exploitation

- [ ] enrichir la chronologie globale avec migrations, contrats, activations,
  suspensions et opérations sur les tables globales ;
- [ ] enrichir la chronologie projet avec recherches, acquisitions, cache,
  scripts, règles, alertes, validations et mises à jour ;
- [ ] désactiver par défaut les endpoints d'écriture ou d'administration ;
- [x] contrôler SSRF, redirections, hôtes, quotas, tailles, pagination et temps
  maximum avant l'exécution ;
- [x] exclure les secrets des contrats V6, clés de cache et paramètres d'action ;
- [x] maintenir le périmètre V6 à des données publiques.

### HDP6-070 — Tests, qualification et livraison

- [ ] tester les contrats de paramètres, réponses et erreurs de chaque endpoint ;
- [ ] tester les dérives de schéma et l'absence de perte de champs bruts ;
- [ ] tester cache, concurrence, revalidation HTTP, reprise et stockage atomique ;
- [x] tester ET/OU imbriqués, fenêtres, séquences, absences, tendances et limites ;
- [ ] prouver qu'une même règle et une même version de données ne répètent jamais
  une action externe ;
- [x] exécuter le diagnostic complet du lot 1 et distinguer tests statiques,
  unitaires, intégration, Docker, appels réels et recette Windows ;
- [ ] corriger ou soumettre tout bug découvert avant de poursuivre ;
- [ ] ne produire archive, EXE et publication `main` qu'à la qualification finale
  explicitement demandée.

### HDP6-080 — Intégration SPIP et publication contrôlée

- [x] consigner l'évaluation validée : équivalence fonctionnelle réalisable sous
  forme hybride, avec SPIP pour l'éditorial et HDP pour les traitements, plutôt
  que par réécriture intégrale du moteur Python/R en PHP ;
- [x] retenir un serveur accessible par Internet, un opérateur HDP unique et des
  données exclusivement publiques ;
- [x] retenir une authentification forte de l'opérateur par passkey ou clé de
  sécurité et des comptes nominatifs protégés pour chaque visiteur ;
- [x] retenir SPIP pour documentation, actualités, curation des flux et alertes,
  ainsi que publication ou partage de projets ;
- [x] imposer une validation manuelle avant toute publication HDP vers SPIP ;
- [x] définir le contrat d'échange versionné HDP–SPIP, ses droits minimaux, son
  journal d'audit et la révocation des jetons ;
- [x] développer le plugin SPIP de consultation/curation et la passerelle de
  brouillons, sans donner à SPIP accès aux runners ni aux secrets HDP ;
- [ ] tester WebAuthn/passkeys, comptes visiteurs, séparation des rôles,
  prévisualisation, validation, retrait et traçabilité des publications ;
- [ ] qualifier l'équivalence écran par écran avant tout remplacement du site HDP.

### HDP6-090 — Veille sanitaire mondiale, RSS et ajout de sources

- [x] définir le périmètre d'exhaustivité mondial et la date de référence afin
  qu'« exhaustif » reste vérifiable et versionné ;
- [ ] rechercher uniquement dans les documentations et registres officiels les
  flux sanitaires, épidémiologiques et d'alertes disponibles par RSS/Atom/API ;
- [x] conserver organisme, pays/région, thème, langue, URL officielle, protocole,
  licence, fréquence, état, preuve documentaire et date de dernière vérification ;
- [ ] détecter doublons, redirections, flux morts, changements de format et
  dérives de schéma sans perdre l'historique ;
- [x] livrer un module d'entrée de nouveau flux avec validation d'URL, aperçu,
  test de parseur, fréquence, projet, activation et désactivation ;
- [x] appliquer les protections SSRF, hôtes autorisés, taille, délai, XML durci,
  déduplication, ETag et Last-Modified avant activation ;
- [x] intégrer les flux validés au catalogue, aux signaux, aux règles et à la
  chronologie, sans assimiler un portail sans flux à un connecteur actif.

### HDP6-100 — Installation, raccourci et bibliothèque locale

- [x] supprimer les attentes indéfinies de `winget` et Docker Compose, journaliser
  l'activité et permettre une annulation contrôlée sans supprimer les volumes ;
- [x] créer en fin d'installation Windows un raccourci Bureau natif vers le
  lanceur de l'instance installée ;
- [x] supprimer le raccourci dans la procédure de désinstallation seulement
  après lecture de sa cible ; le code compile sous MSVC et reste à essayer sur
  Windows avec Docker Desktop ;
- [x] borner la désinstallation aux fichiers exacts du payload après vérification
  d'un marqueur HDP, arrêter Compose sans `-v` et conserver `.env`, données,
  sauvegardes, journaux, volumes et logiciels tiers ;
- [ ] définir séparément le comportement Linux poste et Linux serveur, où un
  raccourci graphique peut être inadapté ou inexistant ;
- [ ] ajouter dans la bibliothèque l'action **Ouvrir le dossier contenant** pour
  le mode poste local uniquement, avec chemin canonique et confinement ;
- [x] pour une instance distante, remplacer l'ouverture d'un chemin serveur par
  une action explicite et autorisée de téléchargement ou d'exploration confinée ;
- [ ] tester chemins avec espaces/Unicode, fichiers supprimés, liens symboliques,
  droits insuffisants et tentative de sortie du répertoire autorisé.

### HDP6-110 — Sauvegardes SQL par périmètre

- [x] conserver la sauvegarde/restauration globale et réussir sa recette dans une
  base temporaire PostgreSQL 16 après les migrations 6.0.0, sans qualifier pour
  autant le déploiement cible ;
- [x] ajouter une sauvegarde cohérente d'un projet incluant ses dépendances,
  fichiers, lignées, règles, cache référencé et chronologie ;
- [ ] ajouter une sauvegarde des signaux, globale ou limitée à un projet et à une
  période, avec règles, évaluations et actions associées ;
- [x] produire manifeste, version de schéma, périmètre, empreintes, inventaire des
  exclusions et contrôle de compatibilité avant restauration ;
- [x] prévalider le bundle sans l'extraire ni restaurer : refuser altération,
  traversée de chemin, lien symbolique, doublon, chiffrement, entrée inattendue
  et dépassement des limites ;
- [x] pour la sauvegarde globale, garantir transaction unique, restauration
  dans une base temporaire, absence de secret dans les commandes et traces,
  refus des collisions sans écrasement, puis suppression obligatoire ;
- [x] fermer le bundle des signaux sur le projet et les règles référencées, puis
  restaurer ses neuf tables dans l'ordre des clés étrangères, en transaction et
  avec refus des champs sensibles ou identifiants dupliqués ;
- [x] prouver à distance la fermeture transitive du bundle projet : séparation
  propriété/dépendance, fichiers confinés adressés par SHA-256, import ordonné,
  collision annulée et base temporaire supprimée ;
- [ ] tester restauration globale, projet isolé, signaux isolés, archive altérée,
  version incompatible et collision d'identifiants.

### HDP6-120 — Lecture et réception de mails

- [ ] arbitrer le mode d'accès : IMAP avec secret d'application, OAuth 2/OIDC ou
  passerelle entrante dédiée ;
- [ ] arbitrer les boîtes/dossiers suivis, pièces jointes autorisées, conservation,
  fréquence, déduplication et rattachement aux projets ;
- [x] séparer réception, analyse, classement, création de signal et brouillon de
  réponse ; aucun envoi ne doit être implicite ;
- [ ] analyser les messages et pièces jointes en environnement borné, sans contenu
  actif, avec quotas, empreinte, provenance et quarantaine ;
- [x] exposer les champs de mail aux règles ET/OU et à la chronologie après
  validation du modèle de données et des obligations de confidentialité ;
- [ ] tester messages multipart, encodages, pièces jointes, doublons, rebonds,
  authentification expirée, boîte indisponible et contenus malveillants.

### HDP6-130 — Méthode de développement guidée

Dernier passage du jalon : **réussi localement et à distance le 24 août 2026**
après qualification des travailleurs d'actions, de travaux de données et de leur
suivi opérateur. Les **267 tests distants** passent sur PostgreSQL 16 sans test
ignoré ; les dix-neuf recettes d'intégration sont seulement ignorées sur l'hôte
local dépourvu de serveur. Les appels connecteurs réels et la recette du
déploiement cible restent des qualifications distinctes.

- [x] traiter les descriptions fonctionnelles comme source du besoin et traduire
  chaque lot en options techniques, effets, risques et critères d'acceptation ;
- [x] ne pas produire automatiquement archive complète ou EXE à chaque étape ;
- [x] diagnostiquer l'application complète après le lot local 1 et consigner les
  contrôles exécutés ou indisponibles ;
- [x] formaliser le jalon réexécutable dans
  `docs/V6_IMPLEMENTATION_GATE.md` et `tools/run_v6_quality_gate.py` ;
- [ ] **tâche récurrente** : reprendre la même boucle diagnostic → questions →
  décision → code → non-régression après chaque nouvelle implémentation V6 ;
- [ ] **tâche récurrente** : mettre à jour `HDP_STATE.json`, la todo-list et le
  changelog après chaque passage du jalon ;
- [ ] revenir vers le propriétaire pour tout bug, ambiguïté fonctionnelle ou
  extension d'autorité avant d'étendre le périmètre.

## Référence de travail 5.2 - décision du 16 août 2026

- [x] désigner **HDP 5.2** comme version de travail active avant le passage 6.0.0 ;
- [x] conserver la version 5.0.2 comme dernière livraison qualifiée et ne pas
  renommer ses EXE, ZIP, empreintes ou documents ;
- [x] publier la décision dans les fichiers canoniques du dépôt privé sans
  force-push ;
- [ ] reconstruire, tester et qualifier séparément les livrables futurs avant de
  les annoncer comme version installable.

## Correctif V5.0.2 - session CSRF locale

- [x] remplacer le marqueur CSRF constant par un jeton dérivé et vérifié en
  double soumission cookie/en-tête ;
- [x] renouveler le cookie CSRF lors de chaque ouverture authentifiée et
  désactiver la mise en cache de l'interface ;
- [x] conserver une transition bornée pour les onglets V5.0.1 déjà ouverts ;
- [x] tester les origines locales, les requêtes intersites, les cookies
  absents/discordants et les méthodes HTTP sûres ;
- [ ] exécuter la recette V5.0.2 sur le poste Windows ayant signalé
  `Origine ou jeton CSRF refusé` et confirmer une mutation depuis l'interface.

## Correctif V5.0.1 - installation Windows/Docker

- [x] corriger l'échec `chmod: Operation not permitted` de `spool-init` sans
  élargir les capacités permanentes des runners ;
- [x] rendre le build R bloquant lorsque `plumber` ou `jsonlite` n'est pas
  réellement disponible dans l'image finale ;
- [x] compiler les sources Windows explicitement en UTF-8 ;
- [x] ajouter les tests statiques et le smoke test Docker associés ;
- [ ] exécuter la recette V5.0.1 sur le poste Windows ayant produit le journal
  d'échec et vérifier l'ouverture de l'interface.

## Round V5 - 16 août 2026

Implémenté et validé localement et par les workflows GitHub :

- [x] HDP-059/060 : validation SQL AST, littéraux préservés, rôle `hdp_reader` ;
- [x] HDP-061 : session locale, Host/Origin/CSRF, retrait des effets de bord GET ;
- [x] HDP-062 : transport anti-SSRF à IP publique épinglée ;
- [x] HDP-063 : cloisonnement UID/groupe de processus/quotas/purge des runners ;
- [x] HDP-064 : versionnement réel lors des réacquisitions ;
- [x] sauvegarde/restauration prévalidée et sans secrets ;
- [x] Data Grid, métadonnées individuelles, plans d’agrégation ;
- [x] SIGNALS, recherche automatique, échéances et snapshots syndromiques ;
- [x] notebooks Jupyter-compatible Python/R ;
- [x] monolithe modulaire simplifié, documentation, UML PDF et Wiki versionné ;
- [x] installateur Linux poste/serveur et workflow de production Windows V5 ;
- [x] 103 tests Python, compilation C stricte, OpenAPI (69 routes), JavaScript et contrôles statiques.
- [x] workflow Windows 2025 réussi, EXE/ZIP V5 récupérés et empreintes contrôlées.

Qualifications d'exploitation encore ouvertes :

- [ ] recette réelle Windows 10/11 avec Docker Desktop ;
- [ ] recette Compose complète (Docker indisponible dans l’environnement local) ;
- [ ] signature Authenticode si un certificat est fourni ;
- [ ] synchroniser le dossier `wiki/` vers le Wiki GitHub séparé ;
- [ ] audit indépendant, test de charge et revue métier des agrégations/signaux.

## Livraison 4.1.0 - 15 août 2026

La version courante individualise la configuration des dix sources, ajoute les
profils techniques et liens officiels, la page Technologies & code et les
exemples cURL/Python/R expurgés. Le contrôle local compte 101 tests Python, deux
scripts JavaScript analysés, un payload de 48 fichiers reconstruit et un EXE
PE32+ GUI x64 contrôlé. Les tâches historiques ci-dessous restent conservées
pour la traçabilité du socle 4.0.0.

Contrôles externes encore utiles : recette Windows 10/11 avec Docker Desktop,
appels représentatifs aux API avec les identifiants autorisés, signature
Authenticode, audit indépendant et choix d'une licence explicite.

Dernière mise à jour : 15 août 2026 — livraison fonctionnelle 4.1.0
Référence de départ : HDP 3.0.0, commit `6eff2065fadc8070be398ecce7560c6d2db44084`  
Référence gelée localement : HDP 4.0.0, commit `0024f5b`  
Branche de référence distante : `main`  
Branche de finalisation : `codex/finalize-hdp-v4`

## Objectif

Ce document centralise les corrections, opérations de qualification et
évolutions futures de HDP. La version 4.1.0 est le gel fonctionnel courant ;
les archives historiques 3.0.0 et antérieures restent immuables. Une tâche
n'est marquée terminée que pour le périmètre effectivement documenté et testé.

## Point d'avancement de la finalisation 4.0.0

Le premier lot est implémenté sur `codex/finalize-hdp-v4` : recherche fédérée,
critères communs et champs propres aux sources, import de données/scripts/documents,
carte des fichiers locaux, planification et périodicité par fichier, accueil lié
au titre, lignée brute et espace SQL PostgreSQL/PostGIS en lecture seule. Les
contrôles locaux réussissent : 82 tests Python, compilation des modules et
analyse syntaxique du JavaScript. Les cases détaillées ne seront clôturées
qu'après documentation, essais d'intégration et qualification finale.

Le deuxième lot ajoute trois connecteurs actifs : HDX HAPI v2 (identifiant
d’application côté serveur), UNHCR Refugee Statistics et GDACS GeoJSON. IOM DTM
et WHO Disease Outbreak News restent des références explicites tant qu’un
contrat d’accès public stable n’est pas configuré. Les contrôles comptent
désormais 85 tests Python réussis.

Le troisième lot livre un moteur de recettes CSV/TSV en flux, avec profilage,
opérations guidées, résultat dérivé, lignée et génération de scripts Python/R.
L’import utilise désormais une publication atomique et contrôle signatures,
archives et macros ; la carte affiche plusieurs couches après vérification de
leur empreinte. Les contrôles comptent 90 tests Python et une analyse
JavaScript réussis.

Le gel fonctionnel 4.0.0 ajoute la chaîne CI, le SBOM CycloneDX, les scripts et
la procédure de sauvegarde/restauration, le prompt global de production, la
documentation utilisateur/API/sécurité/limites et une notice PDF contrôlée sur
27 pages. Les 90 tests, la compilation Python, le JavaScript inline, les
contrôles statiques de sécurité, le runner C17, le payload embarqué et le YAML
Compose ont été vérifiés localement et par GitHub Actions. Le code final est
publié sur la branche privée `main` et l’EXE 4.0.0 a été compilé puis contrôlé
comme PE32+ GUI x64. Les essais Windows/Docker réels, la signature Authenticode,
l'audit indépendant et le choix de licence restent des dépendances externes ou
des opérations de qualification distinctes.

## Convention de suivi

### Priorités

- **P0 — Bloquant** : sécurité, perte de données, installation ou publication.
- **P1 — Important** : fiabilité, maintenance et qualité de production.
- **P2 — Amélioration** : ergonomie, performance ou fonction complémentaire.
- **P3 — Idée** : proposition à qualifier avant planification.

### Statuts

- `À qualifier` : besoin ou périmètre encore à décider.
- `Prêt` : périmètre et critères d'acceptation définis.
- `En cours` : travail actif, avec responsable ou branche identifiée.
- `Bloqué` : dépendance externe explicitement indiquée.
- `Terminé` : changement fusionné, documenté et vérifié.
- `Abandonné` : décision consignée avec sa justification.

## Travaux confirmés

| ID | Priorité | Statut | Mise à jour | Dépendance principale |
|---|---|---|---|---|
| HDP-001 | P0 | Bloqué | Recette complète sur Windows 10/11 x64 avec Docker Desktop/WSL 2 | poste Windows de qualification |
| HDP-002 | P0 | Bloqué | Signature Authenticode de l'installateur | certificat éditeur et service d'horodatage |
| HDP-003 | P0 | À qualifier | Choisir et ajouter une licence HDP | décision du propriétaire |
| HDP-010 | P1 | Terminé | Ajouter une chaîne CI reproductible | validation Linux et compilation Windows réussies sur `main` |
| HDP-011 | P1 | Prêt | Réaliser un audit de sécurité indépendant | environnement d'audit isolé |
| HDP-012 | P1 | En cours | Tester et documenter sauvegarde/restauration | scripts et procédure livrés ; recette réelle à exécuter |
| HDP-013 | P1 | Terminé | Mettre en place l'inventaire des dépendances et licences tierces | SBOM CycloneDX et notices versionnés |
| HDP-014 | P1 | En cours | Durcir la gestion et la rotation des secrets | procédure documentée ; modèle de menace à valider |
| HDP-015 | P1 | En cours | Améliorer le diagnostic Windows et la collecte de journaux expurgés | recette Windows |
| HDP-029 | P1 | En cours | Recherche fédérée sur plusieurs sources depuis le menu Recherche | matrice de capacités pour mots-clés, dates et localisation |
| HDP-030 | P1 | En cours | Consulter et exploiter les fichiers locaux depuis le menu Carte | détection des formats et import géographique sécurisé |
| HDP-031 | P1 | En cours | Créer une planification de téléchargement depuis chaque fichier local | provenance et URL source réutilisables en sécurité |
| HDP-032 | P2 | Terminé | Ajouter une page d'accueil descriptive accessible par le titre du site | navigation et contenu livrés |
| HDP-033 | P1 | Terminé | Importer depuis l'ordinateur des données, scripts et documents de travail | formats autorisés, limites et stockage sécurisé par projet |
| HDP-034 | P1 | Terminé | Afficher et configurer la périodicité de mise à jour pour chaque fichier de données | intervalle v4 documenté ; calendriers avancés au backlog |
| HDP-035 | P1 | Terminé | Ajouter une rubrique « Base SQL » pour consulter PostgreSQL/PostGIS | accès intégré en lecture seule, borné et audité |

### HDP-001 — Recette Windows/Docker

- [ ] tester une installation neuve avec le véritable EXE 3.0.0 ;
- [ ] tester une mise à niveau depuis une installation 2.5.0 représentative ;
- [ ] vérifier la sauvegarde `.env.backup-before-v3.0.0` ;
- [ ] confirmer la conservation de `.env`, des variables inconnues, de `data/`
  et du volume `postgres_data` ;
- [ ] vérifier la santé de PostgreSQL/PostGIS, `api`, `github-api` et du runner
  Python ;
- [ ] vérifier le profil facultatif R ;
- [ ] valider les raccourcis, le choix du port et l'ouverture du navigateur ;
- [ ] archiver les preuves de recette sans secret.

Critère de clôture : rapport daté avec versions Windows/Docker, résultats,
journaux expurgés et empreinte SHA-256 de l'EXE testé.

### HDP-002 — Signature de l'installateur

- [ ] sélectionner un certificat de signature de code ;
- [ ] protéger la clé privée hors du dépôt et des runners ordinaires ;
- [ ] signer l'EXE après sa dernière reconstruction ;
- [ ] appliquer un horodatage de confiance ;
- [ ] vérifier la chaîne de confiance et l'empreinte du fichier signé ;
- [ ] mettre à jour manifeste, documentation et sommes SHA-256.

Critère de clôture : `Get-AuthenticodeSignature` retourne une signature valide
sur le livrable téléchargé.

### HDP-003 — Licence

- [ ] choisir la licence du code HDP ;
- [ ] valider la compatibilité avec les composants tiers ;
- [ ] ajouter `LICENSE` et mettre à jour les notices ;
- [ ] décider si le dépôt peut devenir public.

Le dépôt doit rester privé tant que cette tâche n'est pas terminée.

### HDP-010 — Intégration continue

- [ ] exécuter les 68 tests Python et la compilation des modules ;
- [ ] générer les deux contrats OpenAPI ;
- [ ] analyser JavaScript et Compose/YAML ;
- [ ] compiler et essayer le runner C17 ;
- [ ] reconstruire et contrôler le payload ;
- [ ] compiler ou contrôler l'EXE PE32+ x64 ;
- [ ] effectuer un smoke test Compose/PostGIS lorsque l'environnement le permet ;
- [ ] vérifier les archives et les empreintes de livraison.

Critère de clôture : contrôles obligatoires verts sur une révision identifiée,
sans secret ni artefact non vérifié.

### HDP-011 à HDP-015 — Fiabilité et sécurité

- audit SSRF, redirections, limites de téléchargement et confinement des chemins ;
- audit des runners, du spool, des limites de ressources et de l'absence de shell ;
- audit de la passerelle GitHub et des permissions minimales ;
- essai de restauration du volume PostgreSQL, de `.env` et de `data/` ;
- production d'un SBOM et suivi des versions Python, JavaScript, R et images Docker ;
- procédure de rotation de `GITHUB_TOKEN`, `POSTGRES_PASSWORD` et autres secrets ;
- amélioration du diagnostic Windows sans lecture ni affichage des secrets.

### HDP-029 — Recherche fédérée multi-sources

Le menu « Recherche » doit permettre de lancer une même recherche sur plusieurs
API actives en parallèle, à partir de mots-clés et de critères communs tels
qu'une période et une localisation. Les différences de capacité entre les API
doivent rester visibles : aucun filtre ne doit être annoncé comme appliqué s'il
a été ignoré par une source.

#### Interface utilisateur

- [ ] proposer les modes « Une source » et « Plusieurs sources » dans le menu
  « Recherche » ;
- [ ] permettre de sélectionner au moins deux sources parmi les sept API
  actives, avec actions « Tout sélectionner » et « Effacer » ;
- [ ] proposer les critères communs : mots-clés, date de début, date de fin et
  localisation contrôlée par code ONU M49/ISO3 ;
- [ ] réutiliser HDP-028 pour afficher, dans une zone dépliable, les paramètres
  spécifiques de chaque source sélectionnée ;
- [ ] afficher pour chaque couple source/critère l'état `natif`, `filtré
  localement` ou `non pris en charge` ;
- [ ] empêcher le lancement si aucune source n'est sélectionnée ou si la période
  est incohérente ;
- [ ] afficher la progression, la durée, le nombre de résultats et l'erreur de
  chaque source sans attendre la fin des autres ;
- [ ] offrir deux restitutions : résultats regroupés par source et vue agrégée ;
- [ ] rendre les contrôles utilisables au clavier et sur une largeur réduite.

#### Contrat de recherche

- [ ] définir un objet de requête commun versionné contenant `sources`, `query`,
  `date_from`, `date_to`, `locations`, la limite et les paramètres par source ;
- [ ] établir une matrice de capacités versionnée pour les sept connecteurs ;
- [ ] traduire les critères vers les paramètres natifs de chaque API lorsqu'ils
  existent ;
- [ ] lorsqu'un filtre local est nécessaire, l'appliquer seulement après
  normalisation et le signaler explicitement dans la provenance ;
- [ ] refuser ou signaler clairement un critère impossible à appliquer, sans le
  supprimer silencieusement ;
- [ ] conserver les paramètres effectifs et le mode d'application de chaque
  critère dans la provenance.

#### Exécution parallèle et persistance

- [ ] créer une opération parent de recherche fédérée et une acquisition fille
  indépendante par source ;
- [ ] exécuter les connecteurs avec une concurrence bornée, des délais et des
  reprises propres à chaque source ;
- [ ] préserver les limites, quotas et paramètres globaux de chaque connecteur ;
- [ ] ne pas annuler les acquisitions réussies lorsqu'une autre source échoue ;
- [ ] permettre un résultat global `complet`, `partiel` ou `échoué` ;
- [ ] archiver séparément chaque réponse brute et son empreinte SHA-256 ;
- [ ] agréger les résultats sans perdre la source, l'URL, la date, la
  localisation et l'identifiant d'origine ;
- [ ] dédupliquer seulement selon une règle documentée et réversible ;
- [ ] permettre l'annulation de la recherche sans laisser d'état incohérent.

#### Tests et critères d'acceptation

- [ ] tester la matrice de capacités et la traduction des critères pour chaque
  connecteur ;
- [ ] tester l'exécution concurrente bornée, les délais et les erreurs partielles ;
- [ ] tester les recherches par mots-clés seuls, dates seules, localisation
  seule et critères combinés ;
- [ ] vérifier que la vue agrégée reste traçable jusqu'à l'acquisition source ;
- [ ] vérifier qu'aucun secret ne figure dans la requête, la réponse ou les
  journaux ;
- [ ] documenter les filtres réellement disponibles pour chaque API.

Critère de clôture : depuis le menu « Recherche », l'utilisateur sélectionne
plusieurs sources, saisit des mots-clés et/ou une période et une localisation,
lance une seule opération et obtient des résultats agrégés traçables ainsi que
le statut détaillé de chaque source. Tout critère non appliqué est signalé.

### HDP-030 — Bibliothèque locale dans le menu Carte

Le menu « Carte » doit permettre de parcourir et d'utiliser directement les
fichiers du projet présents dans « Données locales ». Le parcours GeoJSON déjà
disponible — import dans PostGIS, affichage Leaflet et export QGIS/R — doit être
conservé et rendu accessible sans changement de menu.

#### Sélection et identification des fichiers

- [ ] ajouter au menu « Carte » un panneau « Fichiers locaux » alimenté par
  `local_resources` pour le projet actif ;
- [ ] afficher nom, source, format, taille, date, localisation, statut,
  provenance et état de vérification SHA-256 ;
- [ ] filtrer les fichiers par format, source, date, localisation et caractère
  géographique détecté ;
- [ ] permettre la recherche par nom et métadonnées ;
- [ ] identifier explicitement les fichiers `géographiques`, `tabulaires
  géocodables`, `tabulaires` ou `non compatibles avec la carte` ;
- [ ] ne proposer que les fichiers terminés, présents et confinés sous le
  répertoire de données du projet ;
- [ ] vérifier l'empreinte avant import ou signaler clairement qu'elle n'a pas
  encore été contrôlée.

#### Formats et géocodage

- [ ] conserver la prise en charge GeoJSON `Feature` et `FeatureCollection` ;
- [ ] établir une matrice de formats pour GeoPackage, Shapefile ZIP, KML et
  autres formats vectoriels avant de les déclarer compatibles ;
- [ ] détecter dans CSV/XLSX les colonnes latitude/longitude ou les codes
  géographiques ISO3/M49, sans déduire arbitrairement une correspondance ;
- [ ] demander à l'utilisateur de choisir les colonnes, le séparateur, le
  système de coordonnées et la règle de géocodage en cas d'ambiguïté ;
- [ ] afficher un aperçu des colonnes, types, entités et limites spatiales avant
  import ;
- [ ] refuser les projections inconnues ou proposer une conversion explicite
  vers le SRID 4326 ;
- [ ] conserver le fichier original intact et créer une couche dérivée
  traçable dans PostGIS.

#### Utilisation cartographique

- [ ] importer une ressource compatible directement depuis le menu « Carte » ;
- [ ] sélectionner et afficher plusieurs couches simultanément ;
- [ ] activer, masquer, réordonner et supprimer une couche dérivée sans
  supprimer le fichier local d'origine ;
- [ ] régler couleur, contour, opacité, taille des symboles et champ de libellé ;
- [ ] adapter la vue à l'étendue d'une couche ou de toutes les couches visibles ;
- [ ] afficher une légende et une table attributaire bornée ;
- [ ] filtrer les entités par valeur, date et zone lorsque les attributs le
  permettent ;
- [ ] sélectionner une entité sur la carte et afficher ses propriétés avec du
  DOM sûr ;
- [ ] permettre une jointure contrôlée entre une table locale et une couche
  géographique à partir d'une clé choisie par l'utilisateur ;
- [ ] exporter la couche ou la sélection en GeoJSON et dans le paquet QGIS/R ;
- [ ] préserver l'activation volontaire du fond OpenStreetMap et son attribution.

#### Sécurité, limites et provenance

- [ ] conserver les limites de taille, de nombre d'entités et de propriétés ;
- [ ] analyser les archives sans extraction de chemins absolus ou traversée de
  répertoire ;
- [ ] borner l'aperçu tabulaire, les jointures et les requêtes PostGIS ;
- [ ] ne jamais charger automatiquement un fond distant ou une URL contenue
  dans un fichier ;
- [ ] enregistrer ressource source, empreinte, format, projection, options
  d'import, date, nombre d'entités et éventuelles transformations ;
- [ ] signaler séparément les erreurs de lecture, projection, géométrie,
  géocodage et jointure.

#### Tests et critères d'acceptation

- [ ] tester la liste et les filtres des ressources locales dans « Carte » ;
- [ ] tester import, affichage, masquage, ordre et export de plusieurs GeoJSON ;
- [ ] tester fichiers absents, empreintes invalides, formats malformés,
  projections inconnues et archives hostiles ;
- [ ] tester la détection et la confirmation des colonnes géographiques d'un
  fichier tabulaire ;
- [ ] tester qu'une suppression de couche ne supprime jamais la ressource
  locale ;
- [ ] tester clavier, lecteurs d'écran, faible largeur et volumes proches des
  limites autorisées.

Critère de clôture : depuis le seul menu « Carte », l'utilisateur parcourt les
fichiers locaux du projet, identifie ceux contenant des données géographiques,
importe ou géocode explicitement une ressource compatible, affiche et utilise
une ou plusieurs couches, puis exporte le résultat en conservant la provenance
et le fichier original.

### HDP-031 — Planification par fichier depuis Données locales

Chaque fiche de fichier du menu « Données locales » doit proposer une action
« Planifier le téléchargement ». L'utilisateur peut programmer un nouveau
téléchargement à une date donnée ou créer une récurrence pour maintenir la
ressource à jour, sans devoir reconstruire manuellement la recherche d'origine.

#### Interface utilisateur

- [ ] ajouter le bouton « Planifier le téléchargement » sur chaque ressource
  locale dont la provenance permet un nouveau téléchargement ;
- [ ] expliquer pourquoi l'action est indisponible lorsque l'URL ou
  l'identifiant source ne peut pas être réutilisé ;
- [ ] proposer les modes `Une fois` et `Récurrent` ;
- [ ] pour une exécution unique, choisir date, heure et fuseau d'affichage ;
- [ ] pour une récurrence, proposer au minimum intervalle, quotidien et
  hebdomadaire, avec date de début et date de fin facultative ;
- [ ] afficher la prochaine exécution calculée avant validation ;
- [ ] proposer « Télécharger maintenant » depuis la même boîte de dialogue ;
- [ ] afficher sur la fiche le statut, la prochaine exécution, la dernière
  exécution et le dernier résultat ;
- [ ] permettre de suspendre, reprendre, modifier et supprimer uniquement la
  planification, sans supprimer le fichier ;
- [ ] fournir un lien vers l'historique des téléchargements de la ressource.

#### Modèle et provenance

- [ ] étendre les planifications avec un type de cible `resource_refresh` et
  l'identifiant stable de `local_resources` ;
- [ ] conserver source, jeu de données, identifiant distant, URL d'origine,
  paramètres effectifs et acquisition ayant créé le fichier ;
- [ ] distinguer l'URL canonique d'une URL temporaire ou signée ;
- [ ] lorsque l'URL peut expirer, redemander la ressource au connecteur à partir
  de ses identifiants plutôt que de réutiliser aveuglément l'ancienne URL ;
- [ ] enregistrer la planification et tous ses horaires en UTC, puis afficher
  les dates dans le fuseau choisi par l'utilisateur ;
- [ ] rattacher chaque exécution et chaque nouvelle version au projet, à la
  planification et à la ressource logique d'origine.

#### Téléchargement et versionnement

- [ ] réappliquer à chaque passage les contrôles HTTP(S), DNS, redirections,
  taille, chemin confiné et écriture atomique `.part` ;
- [ ] utiliser `ETag` et `Last-Modified` lorsqu'ils sont disponibles ;
- [ ] calculer systématiquement SHA-256 avant de publier une nouvelle version ;
- [ ] enregistrer le résultat `inchangé` lorsque le contenu est identique ;
- [ ] créer une version de fichier lorsque l'empreinte change, sans écraser la
  version précédente pendant le téléchargement ;
- [ ] permettre de désigner la version courante et de télécharger une version
  antérieure conservée ;
- [ ] définir une rétention configurable en nombre de versions ou en durée,
  sans suppression par défaut ;
- [ ] ne jamais remplacer un fichier valide lorsque le nouveau téléchargement
  est incomplet, invalide ou supérieur aux limites ;
- [ ] empêcher deux exécutions simultanées pour la même ressource.

#### Exécution et erreurs

- [ ] réutiliser le planificateur persistant et ses verrous transactionnels ;
- [ ] respecter l'activation globale du connecteur et les limites du projet ;
- [ ] traiter indépendamment les planifications de fichiers différents ;
- [ ] appliquer les reprises configurées sans dépasser les quotas de la source ;
- [ ] distinguer les statuts `planifié`, `en cours`, `inchangé`, `mis à jour`,
  `échoué`, `suspendu` et `expiré` ;
- [ ] conserver une erreur bornée et expurgée, sans jeton ni URL signée complète ;
- [ ] signaler clairement une ressource distante supprimée, déplacée ou devenue
  inaccessible ;
- [ ] ne jamais supprimer le volume, l'acquisition historique ou le fichier
  courant lors d'un échec.

#### Tests et critères d'acceptation

- [ ] tester création unique et récurrente depuis une fiche de fichier ;
- [ ] tester calcul des échéances, fuseaux et changement d'heure ;
- [ ] tester ressource inchangée, nouvelle version, échec réseau, dépassement de
  taille, redirection interdite et URL expirée ;
- [ ] tester le verrou empêchant deux téléchargements concurrents du même fichier ;
- [ ] tester suspension, reprise, modification et suppression de planification ;
- [ ] vérifier que la suppression d'une planification conserve toutes les
  versions déjà téléchargées ;
- [ ] vérifier la traçabilité entre planification, exécution, acquisition,
  ressource logique et version physique.

Critère de clôture : depuis la fiche de chaque fichier éligible dans « Données
locales », l'utilisateur programme un téléchargement unique ou récurrent,
consulte son échéance et son historique, et obtient une nouvelle version
atomique uniquement lorsque le contenu distant a réellement changé.

### HDP-032 — Page d'accueil accessible depuis le titre

HDP doit disposer d'une page d'accueil simple qui présente l'application en
quelques phrases. Le titre « Humanitarian Data Platform » affiché dans l'en-tête
doit devenir un lien cliquable permettant de revenir à cette page depuis toutes
les rubriques.

#### Contenu de la page

- [ ] présenter HDP comme une application locale destinée à rechercher,
  télécharger, organiser et exploiter des données humanitaires et sanitaires ;
- [ ] expliquer en quelques phrases le fonctionnement par projets, les sources
  interrogeables, les données locales, les planifications et la cartographie ;
- [ ] rappeler que l'application fonctionne localement et ne doit pas être
  exposée directement sur Internet ;
- [ ] afficher la version courante de HDP et l'état synthétique des services ;
- [ ] ne mentionner comme disponibles que les fonctions réellement livrées ;
- [ ] conserver un texte court, compréhensible sans vocabulaire technique ;
- [ ] prévoir des accès rapides vers « Recherche », « Données locales »,
  « Planifications » et « Carte » sans surcharger la page.

Texte initial proposé :

> Humanitarian Data Platform vous aide à rechercher et rassembler des données
> humanitaires, sanitaires et géographiques provenant de sources publiques.
> Les résultats sont organisés par projet, conservés avec leur provenance et
> peuvent être téléchargés, planifiés, analysés ou visualisés sur une carte.
> HDP fonctionne localement afin de vous laisser la maîtrise de vos fichiers et
> de vos paramètres.

#### Navigation

- [ ] ajouter une vue `Accueil` à l'interface ;
- [ ] afficher cette vue par défaut lors de l'ouverture de l'application ;
- [ ] transformer le titre du site en véritable lien ou bouton sémantique vers
  l'accueil, disponible dans toutes les vues ;
- [ ] permettre l'activation du lien au clavier avec un focus visible ;
- [ ] associer au lien un libellé accessible explicite, par exemple « Revenir à
  l'accueil de Humanitarian Data Platform » ;
- [ ] synchroniser l'état actif du menu lors du retour à l'accueil ;
- [ ] conserver un comportement cohérent avec les boutons précédent/suivant du
  navigateur si une navigation par fragment ou historique est introduite ;
- [ ] ne pas recharger les services ni perdre le projet sélectionné lors du
  retour à l'accueil.

#### Sécurité, maintenance et tests

- [ ] servir tout le contenu depuis les fichiers locaux, sans script, police,
  image ou suivi externe ;
- [ ] construire les textes dynamiques avec du DOM sûr ;
- [ ] centraliser la version et les libellés pour éviter les divergences ;
- [ ] tester clic, clavier, focus, retour navigateur et affichage initial ;
- [ ] tester l'affichage sur faible largeur et avec un lecteur d'écran ;
- [ ] vérifier que les accès rapides conduisent à la bonne rubrique sans perdre
  le contexte du projet.

Critère de clôture : à l'ouverture de HDP, l'utilisateur voit une courte
présentation fidèle de l'application. Depuis n'importe quel menu, un clic ou
une activation clavier sur le titre du site ramène à cette page sans perdre le
projet actif.

### HDP-033 — Import depuis l'ordinateur

L'utilisateur doit pouvoir sélectionner sur son ordinateur un ou plusieurs
fichiers et les importer dans le projet HDP actif. Le terme « Importer » doit
être utilisé dans l'interface afin de distinguer cette opération d'un
téléchargement depuis Internet.

#### Parcours utilisateur

- [ ] ajouter une action « Importer depuis l'ordinateur » dans « Données
  locales » et des actions contextuelles équivalentes dans « Scripts » et
  « Documents de travail » ;
- [ ] proposer un sélecteur de fichiers et le glisser-déposer, avec import
  multiple ;
- [ ] afficher avant validation le projet cible, la catégorie détectée, le nom,
  la taille et le format de chaque fichier ;
- [ ] permettre de corriger la catégorie et d'ajouter une description ou des
  étiquettes facultatives ;
- [ ] afficher une progression par fichier et pour le lot, permettre
  l'annulation et restituer séparément les succès et les échecs ;
- [ ] rendre les nouveaux éléments immédiatement consultables dans le projet
  sans rechargement de la page.

#### Formats et intégration

- [ ] accepter initialement comme données `CSV`, `TSV`, `XLSX`, `JSON` et
  `GeoJSON`, puis documenter une matrice de prise en charge avant d'ajouter
  d'autres formats géographiques ;
- [ ] enregistrer les données importées dans « Données locales » et les rendre
  disponibles dans « Carte » lorsque leur géométrie ou leurs coordonnées sont
  compatibles avec HDP-030 ;
- [ ] accepter comme scripts de travail `PY` et `R`, ainsi que `SQL`, `SH` et
  `TXT` en stockage ou édition uniquement ;
- [ ] ne jamais exécuter automatiquement un script importé ; seuls les formats
  autorisés par les runners existants peuvent être exécutés ensuite, à la
  demande explicite de l'utilisateur et selon leurs règles d'isolation ;
- [ ] accepter comme documents de travail `PDF`, `DOCX`, `XLSX`, `MD`, `TXT`
  et les formats d'image explicitement autorisés ;
- [ ] ne proposer une prévisualisation que pour les formats rendus de manière
  sûre et laisser tous les documents téléchargeables depuis leur fiche ;
- [ ] créer ou exposer une catégorie « Documents de travail » filtrable dans
  le projet, sans confondre ces documents avec les jeux de données analysables.

#### Stockage, conflits et provenance

- [ ] rattacher chaque import au projet actif avec `origin=user_upload`, nom
  sûr, format détecté, taille, empreinte SHA-256, date et métadonnées utiles ;
- [ ] détecter les doublons par empreinte et proposer « conserver les deux »,
  « créer une nouvelle version » ou « annuler » sans écrasement silencieux ;
- [ ] conserver des versions immuables lorsqu'un fichier importé remplace une
  ressource logique existante ;
- [ ] écrire le flux entrant dans un fichier temporaire `.part`, vérifier son
  intégrité puis publier la version finale par renommage atomique ;
- [ ] isoler strictement les fichiers entre projets et empêcher tout chemin de
  sortir du répertoire de stockage autorisé ;
- [ ] préciser qu'un fichier provenant de l'ordinateur ne possède pas d'URL
  distante : la planification HDP-031 reste indisponible tant qu'une source
  distante explicite et réutilisable ne lui est pas associée ;
- [ ] ne jamais envoyer un fichier importé vers un service externe sans une
  action distincte et explicite de l'utilisateur.

#### Sécurité et limites

- [ ] recevoir les fichiers en flux multipart, sans encodage Base64 dans un
  corps JSON, avec limites par fichier, par lot et par projet ;
- [ ] contrôler conjointement extension autorisée, type MIME déclaré,
  signature du fichier et structure réellement analysée ;
- [ ] normaliser les noms, neutraliser les séparateurs et refuser chemins
  absolus, traversées de répertoire, liens, raccourcis et fichiers exécutables ;
- [ ] refuser les macros ou contenus actifs et ne jamais ouvrir ni exécuter un
  fichier pendant sa détection ;
- [ ] ne pas extraire automatiquement les archives ; tout format composite
  éventuellement ajouté doit être analysé contre les traversées, liens,
  bombes de décompression et dépassements de quotas ;
- [ ] borner les messages d'erreur et supprimer proprement les fragments
  temporaires après échec ou annulation ;
- [ ] confirmer la suppression d'un fichier importé et préserver la trace
  minimale de l'opération selon la politique de conservation.

#### Tests et critères d'acceptation

- [ ] tester tous les formats autorisés, les fichiers vides, trop volumineux,
  tronqués, dupliqués et dont l'extension ne correspond pas au contenu ;
- [ ] tester noms malveillants, traversées de chemin, archives dangereuses,
  contenus actifs et tentative d'import d'un exécutable ;
- [ ] tester import multiple, annulation, échec partiel, concurrence et absence
  de fichier final après un transfert incomplet ;
- [ ] vérifier l'isolation entre projets, la provenance et l'empreinte de chaque
  version ;
- [ ] vérifier qu'aucun script n'est exécuté et qu'aucun document n'est envoyé
  sur le réseau lors de l'import ;
- [ ] tester l'accès clavier, le glisser-déposer, les messages d'erreur et
  l'affichage sur faible largeur.

Critère de clôture : depuis HDP, l'utilisateur sélectionne ou dépose un ou
plusieurs fichiers de son ordinateur, confirme leur catégorie et suit leur
import. Les données, scripts et documents apparaissent ensuite dans le projet
actif avec leur empreinte et leur provenance ; aucun fichier n'est exécuté,
écrasé silencieusement ni transmis à un service externe.

### HDP-034 — Périodicité de mise à jour dans la bibliothèque

La bibliothèque de données, actuellement exposée par « Données locales », doit
présenter pour chaque fichier de données sa périodicité de mise à jour lorsque
la source la publie. La même fiche doit permettre d'activer ou de modifier une
planification de mise à jour sans passer par un autre menu.

#### Affichage par fichier

- [ ] afficher sur chaque ligne ou carte de fichier de données une zone
  « Mise à jour » toujours visible ;
- [ ] y indiquer séparément la périodicité annoncée par la source, la
  planification choisie dans HDP, la dernière vérification et la prochaine
  exécution ;
- [ ] afficher « Non publiée par la source » lorsqu'aucune fréquence fiable
  n'est fournie, sans la déduire d'une simple date de modification ;
- [ ] si une fréquence est estimée à partir d'un historique suffisant,
  l'identifier explicitement comme « Estimation » avec sa méthode et son niveau
  de confiance ;
- [ ] distinguer les états `manuel`, `non disponible`, `planifié`, `suspendu`,
  `à vérifier`, `inchangé`, `mis à jour` et `en erreur` ;
- [ ] rendre l'information accessible dans la vue détaillée comme dans la vue
  compacte de la bibliothèque.

#### Paramétrage depuis la bibliothèque

- [ ] proposer pour chaque fichier l'action « Configurer la mise à jour » ;
- [ ] laisser l'action visible mais désactivée avec une explication lorsque la
  provenance ne permet pas de retrouver la ressource distante ;
- [ ] proposer `Manuelle`, `Selon la source`, `Une fois` et `Personnalisée` ;
- [ ] préremplir « Selon la source » uniquement lorsque le connecteur fournit
  une périodicité exploitable ;
- [ ] permettre au minimum les fréquences quotidienne, hebdomadaire et
  mensuelle, ainsi qu'un intervalle borné, une date de début, une date de fin
  facultative et le fuseau d'affichage ;
- [ ] afficher la prochaine exécution calculée avant confirmation ;
- [ ] permettre de créer, suspendre, reprendre, modifier ou supprimer la
  planification directement depuis la fiche du fichier ;
- [ ] conserver un lien vers l'historique des vérifications et versions.

#### Sources, règles et cohérence

- [ ] ajouter au contrat des connecteurs un champ normalisé de fréquence
  publiée, avec valeur d'origine, unité, date de collecte et URL de preuve
  lorsqu'elle existe ;
- [ ] ne jamais transformer automatiquement la fréquence publiée en tâche
  active : l'utilisateur doit confirmer la planification ;
- [ ] réutiliser les planifications `resource_refresh`, verrous, contrôles de
  provenance, versions immuables et écritures atomiques définis dans HDP-031 ;
- [ ] respecter les quotas, limites et recommandations de chaque API, même si
  l'utilisateur demande une fréquence plus élevée ;
- [ ] avertir lorsque la fréquence choisie est plus courte que celle annoncée
  par la source ou incompatible avec ses quotas ;
- [ ] répercuter une modification de périodicité source sans écraser la
  planification utilisateur et proposer une révision explicite ;
- [ ] appliquer HDP-033 aux fichiers importés depuis l'ordinateur : sans URL ou
  identifiant distant réutilisable, leur mise à jour reste manuelle.

#### Tests et critères d'acceptation

- [ ] tester fréquence publiée, absente, invalide, modifiée et estimée ;
- [ ] tester tous les états et actions depuis les vues compacte et détaillée ;
- [ ] tester calcul des prochaines échéances, fuseaux et changements d'heure ;
- [ ] tester les avertissements de quota et l'impossibilité de contourner les
  limites du connecteur ;
- [ ] vérifier qu'une fréquence source ne crée jamais seule une planification ;
- [ ] vérifier la cohérence entre la bibliothèque, la fiche du fichier et le
  menu « Planifications ».

Critère de clôture : chaque fichier de données possède dans la bibliothèque une
zone « Mise à jour ». L'utilisateur y consulte la périodicité publiée par la
source lorsqu'elle existe, choisit explicitement sa propre planification et
accède à la prochaine échéance ainsi qu'à l'historique, sans duplication du
moteur prévu par HDP-031.

### HDP-035 — Rubrique « Base SQL »

Ajouter au menu principal une rubrique « Base SQL » donnant accès aux données
relationnelles de HDP. La version actuelle repose sur PostgreSQL/PostGIS :
MySQL n'est donc ni nécessaire ni une cible compatible à ajouter pour cette
fonction.

#### Navigation et exploration

- [ ] ajouter l'entrée « Base SQL » au menu principal et aux règles de
  navigation clavier ;
- [ ] ouvrir par défaut un espace « Données du projet » limité au projet actif ;
- [ ] afficher les schémas, vues, tables publiées, colonnes, types, clés,
  relations et index autorisés ;
- [ ] permettre une prévisualisation paginée avec tri et filtres bornés ;
- [ ] fournir une recherche de tables et colonnes ainsi qu'une documentation
  courte des objets applicatifs exposés ;
- [ ] rendre l'accès au schéma technique facultatif, clairement identifié comme
  avancé et expurgé des secrets, jetons et valeurs de configuration sensibles ;
- [ ] conserver le projet sélectionné lors de la navigation vers ou depuis la
  rubrique.

#### Éditeur et résultats SQL

- [ ] intégrer un éditeur prenant en charge `SELECT`, `WITH`, `EXPLAIN` et les
  fonctions PostGIS de lecture autorisées ;
- [ ] fournir des exemples sûrs correspondant aux tables ou vues sélectionnées ;
- [ ] afficher les résultats dans une table paginée avec durée, nombre de lignes
  retournées, troncature éventuelle et messages d'erreur compréhensibles ;
- [ ] permettre l'export explicite du résultat en `CSV`, `JSON` et `GeoJSON`
  lorsque les colonnes sont compatibles ;
- [ ] proposer l'enregistrement volontaire d'une requête comme script SQL du
  projet, sans sauvegarder automatiquement le texte ou l'historique ;
- [ ] permettre l'annulation d'une requête en cours.

#### Accès sécurisé à PostgreSQL/PostGIS

- [ ] faire transiter les requêtes par l'API HDP et ne jamais transmettre au
  navigateur l'hôte, le mot de passe ou la chaîne de connexion de la base ;
- [ ] utiliser un rôle PostgreSQL dédié en lecture seule et une transaction
  `READ ONLY`, indépendamment de la validation syntaxique effectuée par l'API ;
- [ ] refuser les requêtes multiples, DDL, DML, `COPY`, commandes de session,
  accès aux fichiers, extensions, programmes externes et fonctions dangereuses ;
- [ ] appliquer une durée maximale, une limite de lignes, une limite de volume,
  une profondeur de plan et une concurrence bornée ;
- [ ] imposer le périmètre du projet côté serveur, sans dépendre d'un filtre
  fourni uniquement par le navigateur ;
- [ ] journaliser l'empreinte de la requête, sa durée, son statut et son projet,
  sans conserver de résultat sensible ni de secret ;
- [ ] ne pas publier PostgreSQL/PostGIS sur le réseau et conserver le service
  derrière le réseau interne Docker.

#### Outil d'administration externe éventuel

- [ ] ne pas ajouter de dépendance, de lien ou de service MySQL ;
- [ ] privilégier l'explorateur intégré pour les consultations ordinaires ;
- [ ] si un outil d'administration est retenu ultérieurement, utiliser pgAdmin
  ou Adminer configuré pour PostgreSQL, désactivé par défaut, lié uniquement à
  l'interface locale et protégé par une authentification distincte ;
- [ ] ne jamais placer les identifiants de connexion dans l'URL du lien ni dans
  le code de l'interface.

#### Tests et critères d'acceptation

- [ ] tester l'exploration des objets autorisés, la pagination, les filtres et
  les exports ;
- [ ] tester `SELECT`, `WITH`, `EXPLAIN`, fonctions PostGIS autorisées,
  annulation, dépassement de délai et troncature ;
- [ ] vérifier le refus de DDL, DML, requêtes multiples, `COPY`, commandes de
  session et fonctions dangereuses, y compris avec commentaires ou encodages ;
- [ ] vérifier que le rôle SQL ne peut écrire même si la validation de l'API est
  contournée ;
- [ ] vérifier l'isolation des projets et l'absence de secrets dans schémas,
  résultats, erreurs, exports et journaux ;
- [ ] tester navigation clavier, faible largeur et messages destinés aux
  utilisateurs non spécialistes de SQL.

Critère de clôture : la rubrique « Base SQL » permet de parcourir les données
PostgreSQL/PostGIS autorisées du projet, d'exécuter des requêtes de lecture
bornées et d'exporter leurs résultats. Aucune écriture, donnée d'un autre
projet, information de connexion ou exposition réseau directe de la base n'est
possible depuis cette interface.

## Améliorations planifiables

| ID | Priorité | Statut | Mise à jour | Critère synthétique |
|---|---|---|---|---|
| HDP-020 | P2 | À qualifier | Accessibilité de l'interface | navigation clavier, focus, contrastes et lecteurs d'écran testés |
| HDP-021 | P2 | À qualifier | Tests contractuels des connecteurs externes | fixtures versionnées et tests en direct explicitement opt-in |
| HDP-022 | P2 | À qualifier | Détection de dérive des API sources | alerte sans téléchargement ni modification automatique |
| HDP-023 | P2 | À qualifier | Performance des grandes bibliothèques | seuils mesurés et non-régression documentée |
| HDP-024 | P2 | À qualifier | Performance cartographique | limites GeoJSON/PostGIS mesurées et interface réactive |
| HDP-025 | P2 | À qualifier | Export/import contrôlé d'un projet | archive validée, sans secret, avec restauration réversible |
| HDP-026 | P2 | À qualifier | Amélioration du journal de maintenance | historique lisible par version et composant |
| HDP-027 | P2 | À qualifier | Publication GitHub par tag et release | artefacts identiques aux sommes validées |
| HDP-028 | P2 | Terminé | Afficher les paramètres propres à la source dans le panneau Recherche | champs dynamiques, valeurs validées et utilisées pour l'acquisition courante |
| HDP-036 | P1 | Terminé | Unifier le parcours recherche → téléchargement → traitement → export | parcours v4 lié au projet avec provenance |
| HDP-037 | P1 | Terminé | Versionner un contrat de capacités commun à tous les connecteurs | registre 4.0.0 et matrice documentée |
| HDP-038 | P1 | En cours | Finaliser l'extraction des observations des sept sources existantes | filtres métier complets et téléchargements testés sur données réelles |
| HDP-039 | P1 | En cours | Ajouter un portefeuille prioritaire de sources humanitaires officielles | HAPI, UNHCR et GDACS actifs ; IOM DTM référencé |
| HDP-040 | P1 | En cours | Renforcer les sources de surveillance et les dénominateurs sanitaires | OMS/DON, GHO, WorldPop et métadonnées méthodologiques vérifiées |
| HDP-041 | P1 | Terminé | Créer un modèle canonique, des contrôles qualité et une lignée des données | données brutes immuables, normalisées et dérivées traçables |
| HDP-042 | P1 | En cours | Ajouter des traitements guidés et des recettes R/Python reproductibles | moteur CSV/TSV livré ; traitements spatiaux à étendre |
| HDP-043 | P1 | En cours | Traiter les fichiers volumineux sans chargement intégral en mémoire | flux, partitionnement, Parquet/GeoParquet et limites mesurées |
| HDP-044 | P0 | Bloqué | Définir et réussir la recette fonctionnelle finale de HDP | gel local vérifié ; recette Windows/Docker et publication externes |

### HDP-028 — Paramètres spécifiques dans le panneau Recherche

Aujourd'hui, les paramètres spécifiques sont accessibles dans l'onglet
« Paramètres des sources », tandis que le panneau « Recherche » n'affiche que
la source, les mots-clés, la limite et le téléchargement automatique. Le
formulaire de recherche doit aussi permettre de choisir directement les
paramètres propres à la source sélectionnée.

- [ ] générer les champs depuis le `project_schema` du connecteur sélectionné ;
- [ ] afficher uniquement les champs spécifiques, sans dupliquer `query`,
  `result_limit` et `auto_download` déjà présents ;
- [ ] préremplir les champs avec les valeurs enregistrées pour le projet ;
- [ ] actualiser immédiatement les champs lors d'un changement de source ;
- [ ] transmettre les valeurs à `POST /api/acquisitions` pour l'acquisition
  courante ;
- [ ] ne pas modifier silencieusement les valeurs par défaut du projet ;
- [ ] proposer séparément « Enregistrer comme valeurs par défaut » si cette
  persistance est souhaitée ;
- [ ] conserver la prévisualisation sûre de la requête avant exécution ;
- [ ] afficher un message explicite pour ONU/ODD, qui ne possède aucun champ
  spécifique ;
- [ ] restituer clairement les erreurs de validation à proximité du champ ;
- [ ] garantir la navigation clavier, les libellés accessibles et l'affichage
  sur une largeur réduite ;
- [ ] ajouter des tests pour les sept connecteurs et leurs types de champs
  (texte, entier, liste, choix et booléen).

Critère de clôture : pour chacune des sept API actives, un utilisateur peut
sélectionner la source, voir ses paramètres spécifiques, les modifier pour la
recherche courante, prévisualiser la requête puis lancer une acquisition dont
la provenance contient exactement les valeurs validées.

## Feuille de route proposée vers une version fonctionnelle finale

L'objectif final proposé est le suivant : un utilisateur part d'un besoin
métier, recherche simultanément des données adaptées, choisit précisément les
observations à acquérir, conserve les fichiers bruts, produit un jeu normalisé,
applique un traitement reproductible puis consulte, cartographie ou exporte le
résultat sans perdre la provenance.

Parcours cible : Découvrir → Paramétrer → Prévisualiser → Acquérir → Vérifier
→ Normaliser → Traiter → Cartographier ou exporter.

### HDP-036 — Parcours métier unifié

- [ ] transformer chaque opération longue en tâche persistante, annulable et
  reprenable avec les états `préparée`, `en cours`, `partielle`, `terminée`,
  `échouée` et `annulée` ;
- [ ] faire apparaître dans un même écran les sources interrogées, requêtes,
  résultats retenus, téléchargements, contrôles, traitements et exports ;
- [ ] permettre de repartir d'une recherche, d'une acquisition ou d'une version
  de fichier sans ressaisir les paramètres ;
- [ ] distinguer clairement métadonnées trouvées, observations interrogées,
  fichiers téléchargés et jeux de données dérivés ;
- [ ] conserver le projet actif, les filtres et les sélections pendant toute la
  navigation ;
- [ ] fournir un résumé final des succès, éléments ignorés et erreurs par source.

### HDP-037 — Contrat de capacités des connecteurs

Chaque connecteur doit publier un contrat versionné que l'interface peut rendre
sans coder un formulaire particulier pour chaque nouvelle source.

- [ ] déclarer les modes `catalog_search`, `observation_query`,
  `resource_download`, `event_feed` et `geospatial_query` réellement pris en
  charge ;
- [ ] exposer champs communs et champs spécifiques avec types, listes de
  valeurs, dépendances, valeurs par défaut et règles de validation ;
- [ ] déclarer pagination, tri, formats, granularité géographique et temporelle,
  fréquence de mise à jour, quotas, taille attendue et mécanisme
  d'authentification ;
- [ ] publier licence, conditions de réutilisation, citation, niveau de
  sensibilité, date de vérification et état `stable`, `expérimental`,
  `portail uniquement`, `dégradé` ou `retiré` ;
- [ ] fournir une estimation du nombre de résultats et du volume avant les
  téléchargements importants lorsque l'API le permet ;
- [ ] centraliser pagination, reprise après `429/5xx`, cache conditionnel,
  journalisation expurgée et détection de dérive ;
- [ ] empêcher l'interface de promettre une recherche, un téléchargement ou une
  planification que le connecteur ne sait pas réellement exécuter.

### HDP-038 — Finalisation des sept sources existantes

Avant d'élargir fortement le catalogue, les connecteurs HDX/CKAN, ReliefWeb,
OMS/GHO, Banque mondiale, UNICEF/SDMX, ONU/ODD et DHS doivent tous permettre de
passer du catalogue aux observations utiles.

| Source | Paramètres métier à exposer en priorité | Résultat attendu |
|---|---|---|
| HDX/CKAN | pays/zone, organisation, thème, format, licence, date de mise à jour, tags | jeux et ressources téléchargeables |
| ReliefWeb | mots-clés, pays, catastrophe, thème, type de contenu, source, langue, dates | rapports et pièces jointes |
| OMS/GHO | indicateur, pays/région, période, sexe, âge, unité et statut de valeur | observations OData filtrées |
| Banque mondiale | indicateur, pays/région, période, niveau d'agrégation | séries d'observations, pas seulement l'archive mondiale |
| UNICEF/SDMX | flux, dimensions de clé, pays, période, sexe, âge et statut d'observation | série SDMX ciblée en CSV/JSON |
| ONU/ODD | objectif, cible, indicateur, zone, période, sexe, âge et autres ventilations | séries officielles et métadonnées |
| DHS | indicateur, pays, enquête, année, ventilation et sous-groupe | données agrégées publiques ; microdonnées exclues sans autorisation |

- [ ] paginer jusqu'à la limite choisie sans charger arbitrairement un catalogue
  mondial complet ;
- [ ] permettre de sélectionner les colonnes, ventilations et périodes avant
  l'acquisition lorsque la source le permet ;
- [ ] conserver définitions, unités, méthodes, notes, drapeaux de qualité et
  révisions en plus des seules valeurs numériques ;
- [ ] tester un cas positif, vide, paginé, limité, invalide et modifié pour
  chaque source avec fixtures versionnées et test en direct explicitement activé.

### HDP-039 — Portefeuille humanitaire prioritaire

Ordre proposé après HDP-038 :

1. **HDX HAPI** pour des indicateurs humanitaires déjà standardisés et reliés à
   leurs ressources HDX : personnes affectées, déplacements, population,
   sécurité alimentaire, prix, financement, présence opérationnelle et pluie ;
2. **UNHCR Refugee Data Finder API** pour réfugiés, demandeurs d'asile,
   déplacés, apatrides, retours et solutions durables ;
3. **IOM DTM API** pour déplacements internes, opérations, cycles d'évaluation,
   types d'évaluation, origines, motifs et ventilations disponibles ;
4. **GDACS** pour événements de catastrophe, niveaux d'alerte, périodes,
   emprises GeoJSON/KML et flux géographiques ;
5. **ACLED**, uniquement en connecteur facultatif après inscription, OAuth,
   acceptation des conditions et validation des droits d'usage.

- [ ] commencer HDX HAPI avec le statut `expérimental`, car son API se présente
  encore comme bêta ;
- [ ] gérer son identifiant d'application dans la configuration du connecteur,
  sans l'insérer en clair dans les requêtes prévisualisées ou les journaux ;
- [ ] pour chaque source, définir les champs propres, la pagination, les quotas,
  la licence, la citation et les fréquences publiées ;
- [ ] ne jamais contourner l'inscription, les restrictions d'accès ou les
  limites de redistribution ;
- [ ] ne pas multiplier les doublons : lorsqu'une donnée HAPI renvoie vers HDX,
  conserver le lien entre l'observation standardisée et la ressource source ;
- [ ] n'activer une nouvelle source qu'après tests contractuels et scénario de
  téléchargement reproductible.

### HDP-040 — Surveillance sanitaire et dénominateurs

- [ ] ajouter l'API officielle **WHO Disease Outbreak News** comme flux de
  veille, distinct d'une base de cas validée ;
- [ ] conserver OMS/GHO comme source centrale d'indicateurs, avec Athena comme
  voie évaluée lorsque ses dimensions répondent mieux au besoin ;
- [ ] ajouter le **WHO Health Inequality Data Repository** pour les analyses
  d'inégalités seulement après validation de ses jeux et dimensions OData ;
- [ ] intégrer **WorldPop REST/STAC** comme source facultative de population et
  de dénominateurs spatiaux, avec année, produit, résolution et méthode visibles ;
- [ ] maintenir WHO Mortality, GLASS, FluNet/FluID, GHE, UNAIDS, IHME et MICS en
  `portail uniquement` tant qu'aucun contrat d'accès public stable et
  reproductible n'est validé ;
- [ ] ne jamais présenter un article d'alerte, une estimation modélisée ou une
  donnée agrégée comme une observation clinique individuelle ;
- [ ] afficher pour tout dénominateur sa source, année, modèle, résolution et
  compatibilité avec le numérateur.

### HDP-041 — Modèle canonique, qualité et lignée

- [ ] conserver trois niveaux immuables ou versionnés : `raw`, `normalized` et
  `derived` ;
- [ ] créer des entités stables `dataset`, `resource`, `resource_version`,
  `acquisition`, `normalization_run`, `processing_run` et `lineage_edge` ;
- [ ] normaliser sans écraser les champs source : indicateur, valeur, unité,
  période, ISO3/M49, p-code, niveau administratif, sexe, âge, groupe, méthode,
  statut et drapeaux qualité ;
- [ ] harmoniser dates, nombres, valeurs manquantes et géométries tout en
  conservant la valeur originale ;
- [ ] produire automatiquement profil de colonnes, dictionnaire, doublons,
  valeurs manquantes, bornes, unités, couverture temporelle et géographique ;
- [ ] détecter incompatibilités de définitions, ruptures de série, agrégations
  mélangées, années de référence différentes et numérateurs sans dénominateur ;
- [ ] enregistrer pour chaque résultat dérivé les versions exactes des entrées,
  paramètres, code ou recette, environnement, date et empreinte SHA-256 ;
- [ ] reconnaître les anciens fichiers HXL à l'import, sans dépendre des
  services HXL distants retirés par HDX en janvier 2026.

### HDP-042 — Traitements guidés et reproductibles

#### Socle sans code

- [ ] sélectionner, renommer et typer les colonnes ;
- [ ] filtrer, trier, recoder, dédupliquer et traiter explicitement les valeurs
  manquantes ;
- [ ] joindre plusieurs ressources avec diagnostic de cardinalité et lignes non
  appariées ;
- [ ] agréger, pivoter, calculer des groupes, convertir les dates et contrôler
  les unités ;
- [ ] prévisualiser chaque étape, l'annuler et enregistrer la séquence comme
  recette versionnée `JSON` ou `YAML` ;
- [ ] générer en complément un script R ou Python lisible correspondant à la
  recette, sans l'exécuter automatiquement.

#### Recettes de santé publique

- [ ] statistiques descriptives et tableaux par sexe, âge, territoire et
  période ;
- [ ] courbe épidémique, tendance, moyenne mobile et comparaison de périodes ;
- [ ] incidence, prévalence, mortalité, létalité, couverture et ratios seulement
  après validation explicite des numérateurs, dénominateurs, unités et périodes ;
- [ ] intervalles de confiance uniquement lorsque les effectifs, plans ou
  erreurs standards nécessaires sont disponibles ;
- [ ] standardisation sur l'âge uniquement avec population standard choisie,
  classes compatibles et hypothèses affichées ;
- [ ] analyse d'enquête pondérée uniquement lorsque poids, strates et unités
  primaires sont présents et documentés.

#### Recettes humanitaires et spatiales

- [ ] stocks et flux de population, variations, couverture et écarts aux besoins ;
- [ ] population par phase IPC, groupe de déplacement ou niveau administratif ;
- [ ] jointure spatiale, agrégation par COD, distance, zone tampon, densité et
  population exposée ;
- [ ] comparaison de couches seulement après contrôle du système de coordonnées,
  de la date, de la résolution et des limites administratives ;
- [ ] cartes, tableaux et graphiques exportables avec titre, source, période,
  avertissements et méthode.

### HDP-043 — Moteur pour données volumineuses

- [ ] lire et écrire par flux ou blocs, sans chargement intégral en mémoire ;
- [ ] utiliser `Parquet` et `GeoParquet` comme formats dérivés efficaces, tout
  en préservant les fichiers bruts ;
- [ ] évaluer Arrow/DuckDB dans les runners pour filtrage, jointure et agrégation
  locale, sans créer un nouveau service réseau ;
- [ ] charger dans PostgreSQL/PostGIS uniquement les tables ou couches choisies ;
- [ ] afficher estimation de volume, progression, mémoire, espace disque et
  possibilité d'annulation ;
- [ ] définir par mesure les seuils de prévisualisation, pagination, carte,
  import SQL et traitement ;
- [ ] tester reprise après interruption et absence de résultat final partiel.

### HDP-044 — Recette de la version finale

La version ne doit être déclarée finalisée que si les scénarios suivants sont
réussis sur le véritable installateur Windows :

- [ ] lancer depuis « Recherche » une requête par mots-clés, dates et territoire
  sur au moins trois sources compatibles en parallèle ;
- [ ] utiliser dans la même recherche les champs spécifiques de chaque source ;
- [ ] télécharger une série sanitaire tabulaire et une donnée géographique,
  avec licence, provenance, empreinte et version ;
- [ ] planifier leur mise à jour et obtenir une nouvelle version seulement si
  le contenu change ;
- [ ] importer un fichier utilisateur, le normaliser, le joindre à une donnée
  distante et créer un jeu dérivé ;
- [ ] appliquer une recette guidée puis un script R ou Python hors réseau ;
- [ ] consulter le résultat dans la bibliothèque, la carte et la rubrique SQL,
  puis l'exporter ;
- [ ] redémarrer HDP pendant une tâche et vérifier reprise ou échec propre sans
  corruption ;
- [ ] réussir migration 2.5.0, sauvegarde/restauration et non-régression des
  volumes, secrets et archives historiques ;
- [ ] réussir les tests de sécurité réseau, téléchargements, imports, SQL,
  scripts, quotas, chemins et journaux expurgés ;
- [ ] publier une matrice source × fonction × format × test, la documentation
  utilisateur et technique, les limites connues et les empreintes des livrables.

Critère global proposé : un résultat n'est considéré reproductible que si un
autre utilisateur peut, avec les mêmes droits d'accès, relancer la recherche et
la recette à partir des paramètres conservés, identifier les versions exactes
des sources et obtenir le même résultat ou une différence expliquée par une
nouvelle version des données.

### Références officielles vérifiées pour cette proposition

- [HDX HAPI — documentation et couverture](https://hdx-hapi.readthedocs.io/) ;
- [UNHCR Refugee Data Finder API](https://www.unhcr.org/refugee-statistics/insights/explainers/forcibly-displaced-api.html) ;
- [IOM DTM API](https://dtm.iom.int/data-and-analysis/dtm-api) ;
- [GDACS — formats et paramètres d'API](https://www.gdacs.org/floodmerge/data_v2.aspx) ;
- [ACLED — documentation de l'API](https://acleddata.com/acled-api-documentation) ;
- [OMS — GHO OData API](https://www.who.int/data/gho/info/gho-odata-api) ;
- [OMS — Disease Outbreak News API](https://www.who.int/api/news/diseaseoutbreaknews/sfhelp) ;
- [OMS — Health Inequality Data Repository API](https://www.who.int/data/inequality-monitor/data/hidr-api) ;
- [WorldPop — REST API](https://www.worldpop.org/sdi/introapi/) et
  [STAC API](https://stac.worldpop.org/) ;
- [HDX — retrait des services HXL au 31 janvier 2026](https://centre.humdata.org/retiring-hxl-services/).

## Idées nécessitant une décision d'architecture

Ces éléments ne doivent pas être développés sans décision explicite, car ils
modifient le modèle de sécurité ou le périmètre du produit.

| ID | Priorité | Statut | Idée | Risque ou décision requise |
|---|---|---|---|---|
| HDP-100 | P3 | À qualifier | Authentification ou mode multi-utilisateur | nouveau modèle de menace et gestion des rôles |
| HDP-101 | P3 | À qualifier | Exposition sur le réseau local | TLS, authentification, pare-feu et support |
| HDP-102 | P3 | À qualifier | Réseau facultatif pour les scripts | proxy d'egress et allowlist réellement imposée |
| HDP-103 | P3 | À qualifier | Mise à jour automatique de l'application | chaîne signée, retour arrière et conservation des données |
| HDP-104 | P3 | À qualifier | Nouvelles sources hors du portefeuille HDP-039/HDP-040 | stabilité officielle, licence, quotas et sécurité |
| HDP-105 | P3 | À qualifier | Analyse antivirus des téléchargements | moteur, confidentialité et comportement en cas d'alerte |

## Éléments déjà terminés — ne pas rouvrir sans régression démontrée

- [x] version 3.0.0 normalisée dans le code, l'interface et l'installateur ;
- [x] 68 tests Python réussis ;
- [x] API principale : 47 chemins et 63 opérations OpenAPI ;
- [x] passerelle GitHub : 11 chemins et 12 opérations OpenAPI ;
- [x] runner C17 validé sur succès et dépassement de délai ;
- [x] 39 fichiers du payload reconstruits octet pour octet ;
- [x] installateur PE32+ GUI x64 avec ASLR/NX ;
- [x] documentation Markdown, HTML et PDF ;
- [x] archives et sommes SHA-256 vérifiées ;
- [x] publication de `main` sans force au commit `6eff2065…`.

## Modèle pour ajouter une tâche

```markdown
### HDP-XXX — Titre court

- Priorité : P0 | P1 | P2 | P3
- Statut : À qualifier | Prêt | En cours | Bloqué | Terminé | Abandonné
- Version cible :
- Responsable :
- Dépendances :
- Risque principal :

#### Besoin

Décrire le problème observable, sans imposer prématurément une solution.

#### Critères d'acceptation

- [ ] comportement attendu vérifié ;
- [ ] tests de non-régression ajoutés ;
- [ ] documentation et journal mis à jour ;
- [ ] sécurité, migration et conservation des données contrôlées ;
- [ ] livrables et empreintes reconstruits si nécessaire.

#### Preuves de clôture

Commit, résultats de tests, rapport de recette et artefacts concernés.
```

## Règles de gouvernance

1. Ne jamais annoncer une tâche terminée sans preuve reproductible.
2. Toute modification de `source/payload/` impose la reconstruction du payload
   et de l'EXE.
3. Toute modification d'un livrable impose la régénération de ses empreintes.
4. Les migrations restent idempotentes, non destructrices et compatibles 2.5.0.
5. Aucun secret, volume ou fichier utilisateur ne doit être supprimé ou publié.
6. Toute évolution réseau, multi-utilisateur ou automatique exige une revue de
   sécurité avant développement.
7. Les archives historiques restent immuables.
