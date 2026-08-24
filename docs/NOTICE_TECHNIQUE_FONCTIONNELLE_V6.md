# HDP 6.0.0 — notice technique et fonctionnelle de référence

## Statut et périmètre

Cette notice traduit les décisions validées pour la ligne de développement
6.0.0. Elle couvre l'intégration SPIP, le moteur de règles ET/OU, les corrélations
temporelles, les actions contrôlées, l'inventaire exhaustif des connecteurs et
flux sanitaires, le catalogue central, les équivalents fonctionnels, le cache,
les sauvegardes, la réception de mails, l'installation, la bibliothèque,
l'interface, la sécurité et la qualification.

La dernière livraison installable qualifiée demeure HDP 5.0.2. La version 6.0.0
est un développement incrémental du monolithe modulaire existant ; elle ne doit
pas être présentée comme installable avant la fin des recettes Windows, Docker,
sécurité, charge, sauvegarde-restauration et santé publique.

## État d'implémentation de la reprise V6

Le code repris depuis l'archive 5.0.2 contient désormais le moteur de règles,
les migrations du catalogue et du cache, l'import OpenAPI/Swagger, le registre
RSS extensible, les sauvegardes par périmètre, l'authentification passkey, la
passerelle `hdp-spip/1.0`, un plugin SPIP 4.2–4.4 et l'import borné de messages
EML publics, ainsi qu'un travailleur PostgreSQL pour les actions internes. Les
sept recettes de ce travailleur passent sur PostgreSQL 16 distant ; ces éléments
ne constituent pas encore une livraison installable.

Le parcours des règles propose désormais un constructeur visuel de groupes ET/OU,
conditions et corrélations. Chaque modification actualise une formule textuelle et
l'arbre JSON utilisé pour la validation et la simulation. L'édition visuelle est
bornée à cinq niveaux ; un arbre valide plus profond reste disponible dans le mode
JSON avancé et demeure soumis à la limite serveur de douze niveaux.

Le sous-menu de chaque source expose séparément l'inventaire des endpoints, les
paramètres d'entrée, les champs de réponse, les métadonnées documentaires, le
profil technique, l'historique et l'état d'activation. Les portails de référence
sans connecteur stable disposent d'un dossier explicitement non exécutable ;
aucun adaptateur ni secret n'est inventé pour compléter l'affichage.

Les chronologies ne dépendent plus seulement des événements V6 écrits après la
reprise. La portée globale complète l'audit avec les migrations réellement
appliquées, versions de contrats et transitions d'activation. La portée projet
complète l'audit avec les recherches fédérées, acquisitions, exécutions de
scripts, actualisations de ressources et signaux historiques. Une condition de
déduplication évite de répéter un événement déjà présent dans le journal V6.

Trois distinctions restent essentielles : l'importeur exhaustif d'un contrat
ne signifie pas que les inventaires officiels des dix sources sont déjà tous
peuplés ; une planification enregistrée ne signifie pas encore que son adaptateur
réseau générique est exécutable ; l'import EML ne choisit pas le futur protocole
de réception de boîte mail. Les recettes Docker, Windows, PHP/SPIP, appels réels
des connecteurs et restaurations restent séparées.

## Principes validés

1. Les règles combinent des groupes `AND` et `OR` imbriqués, à la fois sur les
   propriétés d'un signal et sur plusieurs événements distincts dans le temps.
2. Les corrélations couvrent comptage dans une fenêtre, séquence ordonnée,
   absence d'un événement attendu, variation et tendance. La référence peut être
   fixe ou glissante selon la règle.
3. Les règles globales sont versionnées, héritées et surchargeables par projet.
   Une nouvelle version globale est proposée au projet et n'est jamais imposée.
4. Les actions sûres peuvent être automatiques dans des limites configurées.
   Tout dépassement devient `pending_approval`. Scripts Python/R, webhooks,
   envois et publications exigent une validation manuelle ; mails et contenus
   SPIP sont d'abord des brouillons.
5. Chaque source inventorie tous ses endpoints officiellement documentés, mais
   leur activation est progressive. L'inventaire ne prouve jamais qu'un endpoint
   est exécutable.
6. Toutes les sources atteignent d'abord le même socle : `discover`, `describe`,
   `search`, `preview`, `acquire`, `refresh`, `provenance`.
7. Si une API ne possède pas une capacité du socle, HDP peut produire un
   équivalent à la demande et le mettre en cache. Les données brutes et la
   provenance sont conservées ; aucune métadonnée absente n'est inventée.
8. Le cache est revalidé par ETag/Last-Modified, fréquence déclarée, durée par
   source, version technique ou forçage utilisateur. Une politique unique
   s'applique à tout le projet. Le défaut fonctionnel validé est
   `stale_if_error`.
9. Le modèle prend en charge durée fixe, multiple de la fréquence source,
   fréquence avec plafond projet et décision manuelle. L'interface recommande
   trois fréquences source avec un plafond de sept jours, sans modifier un projet
   resté en arbitrage manuel avant enregistrement opérateur.
10. La cible SPIP est un serveur Internet : un opérateur unique utilise une
    passkey ou une clé de sécurité ; chaque visiteur possède un compte nominatif.
    Seules des données publiques sont admises et chaque publication est validée
    manuellement.
11. SPIP prend en charge documentation, actualités, curation des flux et alertes,
    ainsi que publication ou partage de projets. L'équivalence est techniquement
    réaliste par une architecture hybride : plugin SPIP côté éditorial et API HDP
    côté traitements. Réécrire les runners et connecteurs en PHP augmenterait les
    risques sans bénéfice fonctionnel.
12. L'inventaire sanitaire mondial est versionné et fondé sur les preuves
    officielles disponibles à une date donnée. Un module permet d'ajouter et de
    tester de nouveaux flux sans les activer implicitement.
13. Les sauvegardes SQL couvrent l'instance entière, un projet ou les signaux.
    Pour les signaux, l'opérateur choisit des UUID du projet actif, le projet
    entier ou tous les projets, avec une période optionnelle dont le début est
    inclus et la fin exclue. La bibliothèque peut ouvrir le dossier contenant
    un fichier seulement en mode poste local et dans un répertoire confiné.
14. La réception de mails est séparée de tout envoi. Messages et pièces jointes
    sont bornés, tracés et rattachables aux projets avant d'être exposés aux règles.
15. Une étape de développement ne produit pas automatiquement un EXE ou une
    archive. Elle se termine par un diagnostic complet et une discussion de tout
    bug ou arbitrage restant.

## Intégration SPIP

SPIP devient la couche éditoriale et de consultation protégée. HDP demeure le
service de collecte, catalogue, règles et traitements. Le plugin échange avec
une API dédiée, à droits minimaux, et ne reçoit aucun secret de connecteur ni
accès aux runners. HDP crée uniquement un brouillon versionné ; la publication,
la mise à jour et le retrait sont des décisions humaines auditées.

L'implémentation utilise un jeton de service limité aux portées
`publication:pull` et `publication:ack`. Seule son empreinte est conservée dans
HDP, le secret n'est affiché qu'à la création et sa révocation est immédiate.
Le plugin vérifie le contrat, l'empreinte canonique et la classification
`public`, puis publie dans des pages sans cache partagé visibles uniquement par
un auteur SPIP connecté. L'opérateur approuve toujours le brouillon dans HDP
avec sa session passkey avant que SPIP puisse le récupérer.

Cette architecture peut fournir un site fonctionnellement équivalent tout en
conservant les mécanismes Python/R, PostgreSQL/PostGIS et Docker. Une conversion
« plugin SPIP pur » reste possible en théorie mais demanderait une réécriture
disproportionnée et créerait deux moteurs techniques difficiles à qualifier.

## Architecture cible

### Règles

- `rule_definitions` porte l'identité, la portée, l'état et la version courante.
- `rule_versions` conserve un arbre JSON immuable, son empreinte et sa date.
- `rule_inheritance` relie modèle global, version proposée et surcharge projet.
- `rule_evaluations` enregistre fenêtre, événements, références, résultat et
  preuve d'évaluation.
- `action_requests` sépare la décision de l'effet, avec niveau de risque, limites,
  statut et clé d'idempotence.
- `action_executions` conserve le résultat, les erreurs, les empreintes et la
  chronologie.
- Le travailleur interne réclame une seule demande par transaction avec
  `FOR UPDATE SKIP LOCKED`, pose un bail borné et reprend les baux expirés sans
  exécuter deux fois le même effet. Chaque effet possède en plus une contrainte
  unique sur `request_id`.
- Les notifications, classifications et tâches sont des objets HDP internes. Les
  courriels et publications ne deviennent que des brouillons. Les recherches et
  actualisations sont mises dans `automated_data_jobs`. Un second travailleur les
  réclame avec bail, exécute uniquement les sources explicitement nommées via les
  adaptateurs HDP existants et conserve un résultat par source. Les recettes
  PostgreSQL sont vérifiées ; les appels Internet réels restent une preuve
  distincte.
- Une annulation observée avant l'effet termine la tentative sans créer d'objet.
  Les quotas du projet sont relus sous verrou juste avant l'effet et peuvent
  replacer la demande en `pending_approval`.
- Un travail de données conserve les sources déjà réussies pendant ses reprises.
  Une acquisition est unique pour le couple travail/source ; une annulation est
  observée avant chaque source, mais ne prétend pas interrompre un transfert HTTP
  déjà engagé tant que la recette réseau correspondante n'est pas qualifiée.
- La vue **Actions & travaux** expose par projet les décisions, toutes les
  tentatives, les brouillons associés et les résultats de chaque source. Elle ne
  permet une approbation, un rejet ou une annulation qu'après confirmation et
  saisie d'un motif opérateur.

Une règle est un arbre composé de groupes logiques et de feuilles `condition` ou
`correlation`. Le schéma est versionné, strict, borné et validé côté serveur.

### Connecteurs et catalogue

- `source_api_versions` conserve famille, version, documentation, empreinte et
  période de validité.
- `source_endpoints` conserve méthode, chemin, authentification et état
  d'activation.
- `endpoint_parameters` décrit les paramètres officiels et leur support HDP.
- `response_fields` décrit tous les chemins documentés ou observés.
- `raw_metadata_snapshots` conserve les métadonnées brutes immuables.
- `catalog_records` fournit les métadonnées normalisées et les liens vers le brut.
- `connector_capabilities` décrit le socle fonctionnel et son niveau de support.

Les états d'un endpoint vont d'inventorié à actif, puis éventuellement suspendu
ou obsolète. Chaque changement de contrat est comparé à la version antérieure et
soumis à validation avant activation.

### Équivalents et cache

Un équivalent peut construire un catalogue, matérialiser une API paginée en
JSON/Parquet/CSV, inférer un schéma observé avec confiance, produire un aperçu,
comparer des versions ou normaliser une géographie. Le brut précède toujours la
normalisation.

La clé de cache comprend source, version d'API, endpoint, paramètres canoniques,
format, version du connecteur et version de transformation. Elle ne contient ni
secret ni valeur sensible. L'écriture est temporaire, vérifiée, puis atomique.

## Interface attendue

Chaque encart de source propose **Paramétrages**, avec les portées globale et
projet. Les vues exposent Endpoints, Paramètres d'entrée, Champs de réponse,
Métadonnées, Technique et Historique, ainsi que les liens vers le portail, la
documentation, l'API et le fichier de configuration en lecture.

Le constructeur de règles permet d'ajouter conditions et sous-groupes, de
basculer chaque groupe entre ET et OU, d'afficher l'arbre et la formule, puis de
simuler la règle sans action. Le détail d'évaluation montre les événements
retenus, les conditions vraies ou fausses et la référence de tendance.

Le catalogue sanitaire expose des formulaires générés depuis les contrats :
cases à cocher et listes pour les valeurs contraintes, champs typés pour les
valeurs libres. Les flux RSS/Atom/API ajoutés passent par aperçu, validation et
activation séparée. La bibliothèque n'offre l'ouverture du dossier natif qu'en
mode poste local ; une instance distante propose téléchargement ou exploration
serveur confinée.

## Sauvegardes et mails

Les sauvegardes sont des ensembles cohérents et manifestés. Le périmètre projet
inclut ses dépendances et le périmètre signaux inclut événements, règles,
évaluations et demandes d'action correspondantes. Une restauration est d'abord
prévalidée et ne remplace aucune donnée silencieusement. La prévalidation
vérifie sans extraction le confinement des chemins, les doublons, liens,
chiffrement, limites, inventaire, tailles et empreintes. Elle ne restaure rien
et ne constitue jamais une autorisation automatique. Pour le périmètre global,
une action séparée exige une confirmation littérale, crée une nouvelle base au
nom aléatoire, refuse toute collision, restaure en transaction unique, vérifie
migrations et tables puis supprime obligatoirement la base temporaire. La recette
PostgreSQL réelle est automatisée dans la CI et demeure une preuve distincte du
jalon local. Le périmètre signaux transporte aussi son projet parent et ses
règles référencées ; neuf tables sont importées dans l'ordre de leurs clés
étrangères, au sein d'une transaction, avec refus des champs sensibles et des
collisions. Pour le périmètre projet, une sélection temporaire ferme les
dépendances de clés étrangères sans suivre vers les autres projets les objets
globaux partagés. Les fichiers physiques référencés sont confinés, refusent les
liens symboliques, sont dédupliqués par SHA-256 et reliés à leurs chemins stockés.
Cette fermeture projet a réussi sa recette PostgreSQL 16 distante, y compris le
fichier physique et le rollback d'une collision enfant ; la qualification du
déploiement Windows/Docker reste une porte distincte.

La désinstallation Windows candidate exige un marqueur créé par l'installateur.
Elle arrête les services par Compose sans option de suppression de volumes,
supprime uniquement les fichiers exacts du payload et ne retire le raccourci que
si sa cible appartient au dossier sélectionné. `.env`, données, sauvegardes,
journaux, volumes PostgreSQL et logiciels tiers sont conservés. Ce contrat de
code ne remplace pas une recette réelle sur Windows 10/11 avec Docker Desktop.

Le connecteur réseau de réception de mails reste à arbitrer entre IMAP, OAuth et
passerelle entrante. Le premier socle implémenté importe manuellement un fichier
EML dont le caractère public est confirmé et prouvé par une URL HTTPS. Il
déduplique, borne corps et pièces jointes, refuse les extensions exécutables,
masque les adresses, supprime les paramètres d'URL et conserve les fichiers dans
un stockage adressé par contenu. Faute de moteur antimalware dans l'environnement,
chaque téléchargement non analysé exige une confirmation explicite. Seul le
rattachement manuel à un projet crée un signal et déclenche les règles. Aucun
envoi automatique n'est inclus.

## Sécurité et exploitation

- Réserver la clé d'idempotence avant notification, téléchargement ou webhook.
- Utiliser une file de travaux pour séparer évaluation et exécution.
- Ne jamais faire réclamer par le travailleur interne les types `python_script`,
  `r_script` ou `webhook`, même après une approbation enregistrée ; leur exécuteur
  sécurisé reste indisponible.
- Conserver `network_mode: none` pour les runners tant qu'aucun egress réel,
  contrôlé et auditable n'est disponible.
- Versionner le code Python/R et vérifier son SHA-256 avant exécution.
- Désactiver les endpoints d'écriture et d'administration par défaut.
- Contrôler SSRF, redirections, hôtes, quotas, tailles, pagination et durées.
- Ne jamais exposer les secrets dans les contrats, clés, journaux ou aperçus.
- Sur Internet, exiger WebAuthn avec vérification utilisateur, une origine HTTPS
  exacte, une session opaque dont seule l'empreinte est stockée et des cookies
  `Secure`, `HttpOnly` et `SameSite=Strict` selon leur rôle.
- Limiter le périmètre fonctionnel à des données publiques.
- Conserver le constat d'exploitation : les runners Python/R et leur réseau
  demeurent indisponibles tant que l'infrastructure d'exécution n'est pas active ;
  `network_mode: none` ne simule aucune allowlist.
- Distinguer l'accès GitHub applicatif du dépôt de développement : le dépôt privé
  existe et son accès par connecteur a été vérifié, mais aucun jeton n'est injecté
  dans l'application et aucune publication 6.0.0 n'a été effectuée.

## Qualification

La recette couvre les contrats, les dérives de schéma, la fidélité de
normalisation, le cache concurrent, les règles temporelles, l'idempotence, la
sécurité et la non-régression 5.x. Chaque lot commence et se termine par un
diagnostic complet. Un état n'est « terminé » que si le code, la migration, les
tests et la preuve correspondante existent.

Cette procédure est récurrente : elle doit être intégralement répétée après
chaque nouvelle implémentation V6. Le jalon canonique est décrit dans
`docs/V6_IMPLEMENTATION_GATE.md` et exécuté par
`tools/run_v6_quality_gate.py`. Un échec automatisable arrête le lot ; une
recette Docker, Windows ou distante indisponible reste explicitement ouverte et
interdit seulement de revendiquer la qualification correspondante.
