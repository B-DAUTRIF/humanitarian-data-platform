# Journal des versions

## 6.0.0-dev - file d'actions interne - 24 août 2026

- séparation effective entre évaluation, demande et travailleur asynchrone ;
- réclamation PostgreSQL concurrente avec bail, `SKIP LOCKED`, reprise des baux
  expirés, tentatives bornées et temporisation progressive ;
- annulation transactionnelle avant tout effet et nouvelle vérification des
  limites projet au moment de l'exécution ;
- effets idempotents pour notifications internes, classifications, tâches HDP,
  brouillons et mise en file des recherches/actualisations ;
- scripts Python/R, webhooks et tout effet réseau maintenus hors des exécuteurs
  automatiques ;
- 257 tests recensés localement, dont sept nouvelles recettes PostgreSQL
  réservées à la CI distante.

## 6.0.0-dev - fermeture transitive des projets - 24 août 2026

- remplacement de l'inventaire manuel du projet par une fermeture transitive
  des clés étrangères dans une transaction répétable ;
- distinction entre lignes possédées par le projet et dépendances globales
  partagées : les enfants sans `project_id` sont suivis depuis les objets
  possédés, mais les références d'autres projets ne sont jamais aspirées ;
- exclusion explicite des sauvegardes et des tables d'authentification opérateur ;
- collecte confinée, sans lien symbolique, des fichiers d'acquisition, ressources,
  artefacts, rapports de scripts, caches et pièces jointes ; déduplication par
  SHA-256 et inventaire de toutes les références d'origine ;
- restauration des tables dans l'ordre des dépendances, vérification exacte des
  références de fichiers et suppression obligatoire de la base temporaire ;
- ajout de deux recettes PostgreSQL réelles couvrant cinq tables transitives,
  un fichier physique et le rollback d'une collision projet ;
- 247 tests découverts localement, 241 réussis et six tests PostgreSQL réservés
  à la CI ; 247/247 tests ensuite réussis à distance après correction de la
  recette de collision pour conserver la règle d'un projet unique par bundle.

## 6.0.0-dev - restauration isolée des signaux - 24 août 2026

- ajout du projet parent et des règles de signaux référencées au bundle signaux,
  afin que son inventaire de neuf tables soit fermé sur ses clés étrangères ;
- clonage du schéma courant sans données dans une base PostgreSQL neuve, calcul
  de l'ordre topologique des tables et import JSONL intégral dans une transaction ;
- refus des fichiers inattendus, colonnes divergentes, lignes trop volumineuses,
  champs sensibles, comptages incohérents et collisions d'identifiants ;
- suppression obligatoire de la base temporaire après succès comme après échec ;
- ajout de deux recettes PostgreSQL réelles : restauration des neuf tables dans
  l'ordre des dépendances et rollback non destructif d'un identifiant dupliqué ;
- 244 tests découverts localement, 240 réussis et quatre tests PostgreSQL
  explicitement réservés à la CI ;
- restauration projet maintenue bloquée à ce jalon historique, avant le lot de
  fermeture transitive suivant.

## 6.0.0-dev - restauration PostgreSQL temporaire - 24 août 2026

- ajout d'un chemin de restauration globale exigeant la confirmation littérale
  `RESTORE_IN_TEMPORARY_DATABASE` et n'autorisant jamais une restauration
  automatique ;
- contrôle exact de la version applicative, des migrations, de l'inventaire et
  de l'empreinte avant toute création de base ;
- création d'une base PostgreSQL au nom aléatoire, refus des collisions sans
  suppression, `pg_restore` en transaction unique, vérification des migrations
  et des tables, puis suppression obligatoire de la base temporaire ;
- ajout de `POST /api/v6/backups/{backup_id}/restore/temporary` et d'une trace
  d'audit ne contenant ni secret ni nom de base temporaire ;
- ajout d'une recette CI PostgreSQL 16 avec dump et restauration réels, contrôle
  de suppression et contrôle de non-écrasement en cas de collision ;
- jalon local : 241 tests découverts, 239 réussis et deux recettes PostgreSQL
  explicitement ignorées faute de serveur local ; leur exécution distante reste
  requise avant de déclarer cette porte qualifiée ;
- restauration globale ensuite prouvée par 241/241 tests sur PostgreSQL 16 ;
  restaurations projet et signaux encore distinctes à ce jalon historique.

## 6.0.0-dev - prévalidation des sauvegardes - 24 août 2026

- ajout d'une prévalidation ZIP bornée avant toute restauration : chemins,
  doublons, liens symboliques, chiffrement, inventaire, tailles et empreintes ;
- ajout de `POST /api/v6/backups/{backup_id}/prevalidate`, qui ne restaure rien
  et ne transforme jamais une validation réussie en autorisation automatique ;
- mutualisation du contrôle du chemin confiné et de l'empreinte du bundle
  enregistré entre téléchargement et prévalidation ;
- tests d'une archive valide, d'un fichier altéré, d'une traversée de chemin,
  d'entrées dupliquées, d'un lien symbolique et d'un dépassement de taille
  décompressée ;
- restauration PostgreSQL temporaire, collisions et compatibilité de schéma
  toujours non qualifiées et explicitement reportées au prochain sous-lot P0.

## 6.0.0-dev - reprise et cohérence des preuves - 24 août 2026

- vérification de l'artefact GitHub Actions V6 et de ses empreintes avant toute
  reprise du développement ;
- nouvelle exécution locale du jalon V6 avec 232 tests Python, 67 fichiers
  Python analysés, 19 migrations et 161 instructions SQL validées ;
- distinction explicite entre le jalon CI distant de 231 tests et le jalon local
  augmenté par le nouveau contrôle de traçabilité ;
- mise à jour de `HDP_STATE.json` avec la branche, le commit, la PR, les
  workflows et les empreintes réellement vérifiés ;
- ajout d'un contrat automatisé empêchant que le nombre de tests ou
  l'inventaire Python versionnés divergent à nouveau du dépôt ;
- aucune publication, fusion, reconstruction d'artefact ou qualification
  Windows, Docker, PHP/SPIP et connecteurs réels.

## 6.0.0-dev - règles et catalogue central - 21 août 2026

- passage officiel de la ligne de travail 5.2 à HDP 6.0.0 en développement ;
- intégration de la notice technique et fonctionnelle dans la todo-list ;
- intégration des lots SPIP, veille sanitaire mondiale/RSS, installation et
  bibliothèque, sauvegardes par périmètre, réception de mails et méthode de
  diagnostic incrémental ;
- ajout d'un jalon de qualité automatisé et obligatoire à répéter après chaque
  nouvelle implémentation V6, avec blocage explicite en cas d'échec ;
- fiabilisation du futur installateur V6 : commandes longues bornées, lecture de
  sortie non bloquante, activité périodique et annulation contrôlée sans
  suppression des données ou volumes existants ;
- premier lot local du moteur ET/OU versionné : validation bornée, simulation
  avec preuve, comptage, séquence, absence et tendance fixe ou glissante ;
- migrations du catalogue central, des contrats de connecteurs, du cache, des
  politiques projet, des demandes d'action idempotentes et de la chronologie ;
- validation et comparaison des contrats de connecteurs, clé de cache canonique
  sans secret et politique `stale_if_error` configurable par projet ;
- 17 chemins API V6 et première interface experte pour les règles, les paramètres
  des sources et la politique de données périmées ;
- corrections de compatibilité V5 sur `lookback_hours`, l'idempotence des actions,
  l'identifiant des métadonnées et les critères de disponibilité à l'agrégation ;
- import exhaustif des contrats OpenAPI/Swagger documentés, historique
  d'activation progressive et affichage de tous les paramètres/champs inventoriés ;
- catalogue central fidèle avec instantanés bruts, champs non mappés, lignée,
  confiance, références projet et planifications versionnées ;
- matérialisation d'équivalents à la demande et cache public partagé,
  adressé par contenu, atomique et revalidable par ETag/Last-Modified/fréquence ;
- registre de 15 flux officiels ReliefWeb, OMS, ECDC et CDC, plus cycle complet
  de proposition, aperçu réseau borné, validation manuelle et abonnement ;
- sauvegardes globales PostgreSQL, projet et signaux avec manifeste et
  empreintes, sans autorisation de restauration automatique ;
- authentification opérateur WebAuthn/passkey, session opaque hachée, cookies
  stricts, suppression du secret des URL et écran d'enrôlement initial ;
- contrat `hdp-spip/1.0`, jetons limités et révocables, brouillons publics à
  validation manuelle et plugin de consultation protégée pour SPIP 4.2 à 4.4 ;
- import EML public sans connexion à une boîte : masquage des adresses,
  pièces jointes bornées et confinées, rattachement manuel puis règles V6 ;
- interface ajoutée pour SPIP, sauvegardes, courriels, flux personnalisés,
  chronologies global/projet, paramètres exhaustifs et exploration confinée ;
- installateur fiabilisé avec délais, annulation et raccourci Bureau ; les
  lanceurs n'inscrivent plus le secret d'installation dans l'URL ;
- diagnostic local courant : 19 migrations et 49 chemins API V6 avant le
  dernier passage documentaire ;
- l'inventaire officiel effectivement peuplé pour les dix API, l'exécution des
  planifications du catalogue, le connecteur réseau de mails, les exécuteurs
  d'actions et le constructeur visuel de règles restent à terminer ;
- recettes Docker, Windows, PHP/SPIP, appels connecteurs réels et restaurations
  non exécutées dans cet environnement ;
- conservation de 5.0.2 comme dernière livraison installable qualifiée.

## 5.2 - référence de travail - 16 août 2026

- choix explicite de **5.2** comme version de travail active avant le passage à
  la ligne 6.0.0 ;
- conservation de **5.0.2** comme dernière livraison applicative et dernier
  installateur qualifiés.

## 5.0.2 - renouvellement de la session CSRF locale - 16 août 2026

- remplacement du marqueur CSRF constant par un jeton dérivé du secret local,
  vérifié en double soumission entre cookie et en-tête HTTP ;
- renouvellement du cookie CSRF à chaque ouverture authentifiée et interdiction
  de mise en cache de la page d'application et de la redirection d'amorçage ;
- compatibilité transitoire avec les onglets 5.0.1 déjà ouverts, toujours
  bornée par les contrôles Host, Origin, Fetch Metadata et SameSite strict ;
- message de récupération explicite lorsque l'interface chargée est périmée ;
- tests unitaires ajoutés pour les origines, requêtes intersites, cookies et
  méthodes HTTP sûres.

## 5.0.1 - correctif d'installation Windows/Docker - 16 août 2026

- correction de l'initialisation du volume `execution_spool` : les permissions
  sont désormais appliquées avant le propriétaire non privilégié, sans ajouter
  la capacité Linux `FOWNER` ;
- installation R rendue vérifiable : dépôt binaire Rocker conservé, dépendances
  système complétées et build arrêté si `plumber` ou `jsonlite` manque ;
- compilation MSVC forcée en UTF-8 afin de supprimer le texte français
  mojibaké dans l'interface et les journaux ;
- ajout d'une recette CI construisant réellement l'image R, vérifiant ses
  paquets et exécutant `spool-init` sur un volume Docker neuf ;
- version de maintenance portée à 5.0.1, sans migration destructive.

## 5.0.0 - intelligence HDX et sécurité locale - 16 août 2026

- HDX Data Grid, métadonnées jeu/fichier et plans d’agrégation ;
- SIGNALS, actions automatiques à échéance et surveillance syndromique ;
- notebooks Jupyter-compatible exécutés dans les runners Python/R ;
- P0 SQL, API locale, SSRF, runners, sauvegarde/restauration et rafraîchissement corrigés ;
- monolithe modulaire simplifié, documentation/UML/Wiki et distributions Windows/Linux.

## 4.1.0 - configuration individualisée et hub technique - 15 août 2026

- dix contrats globaux indépendants, limites HTTP et propriétés fixes par source ;
- profils techniques et liens officiels contextualisés pour les dix connecteurs ;
- prévisualisations cURL, Python `httpx` et R `httr2` sans secret ;
- page utilisateur de 25 ressources, 13 catégories et 87 liens ;
- distribution du code et des livrables dans un dossier Google Drive vérifié ;
- compatibilité des paramètres et sauvegardes 4.0.0 ;
- 101 tests automatisés et documentation consolidée 4.1.0.

## 4.0.0 — gel fonctionnel — 15 août 2026

- recherche fédérée, critères communs et champs spécifiques ;
- dix connecteurs actifs avec HAPI, UNHCR et GDACS ;
- import atomique, périodicité et planification par ressource ;
- accueil, carte multi-couches et SQL en lecture seule ;
- recettes CSV/TSV, scripts Python/R et lignée dérivée ;
- CI, SBOM, sauvegarde/restauration et documentation 4.0.0 ;
- installateur Windows laissé à recompiler et qualifier faute de
  compilateur/Windows/certificat.

## 3.0.0 — version finale — 15 août 2026

- Gel du contrat applicatif et suppression des libellés de préversion.
- Intégration complète de la passerelle REST GitHub apparue sur `main` en 2.4.1,
  renforcée par un conteneur non privilégié et des écritures désactivées par défaut.
- Documentation finale consolidée : cahier des charges, architecture, sécurité,
  référence API, guide HTML/PDF et prompt global de production.
- Reconstruction de l'installateur Windows, des archives source/utilisateur et
  de l'archive complète avec manifeste et empreintes SHA-256.

## 3.0.0 — itération 2 — 15 août 2026

- Exécution Python/R par versions immuables dans des runners distincts,
  non privilégiés, sans réseau et avec limites de temps, processus et sortie.
- Rapports JSON d'exécution avec empreintes SHA-256 et historique par script.
- Registre de quatre flux RSS officiels ReliefWeb, abonnements planifiés,
  déduplication, requêtes conditionnelles et parseur XML durci.
- Vue chronologique de type Gantt par projet.
- Import GeoJSON dans PostGIS, visualisation Leaflet 1.9.4 embarquée et exports
  QGIS/R ; fond OpenStreetMap activé uniquement à la demande.
- Politique GitHub actualisée pour les jetons finement granulés et l'API REST
  versionnée 2026-03-10.
- 47 chemins et 63 opérations dans le contrat OpenAPI généré.

## 3.0.0 — itération 1 — 14 août 2026

- Registre versionné des paramètres pour les sept connecteurs API.
- Paramètres globaux et modèles propres à chaque source et projet.
- Prévisualisation assainie des URL/commandes sans appel réseau.
- Paramètres effectifs archivés avec acquisitions et planifications.
- Métadonnées et filtres initiaux de bibliothèque.
- Migrations idempotentes enregistrées, conservation renforcée de `.env`.
- Chaîne Windows portée en 3.0.0 ; recette réelle reportée au jalon final selon D09=B.
- 52 tests Python réussis, plus syntaxe Python/JavaScript et roundtrip du payload.

## 2.5.0 — 7 août 2026

- Catalogue intégré de 18 sources sanitaires et épidémiologiques mondiales.
- Connecteurs interrogeables et planifiables ajoutés pour OMS/GHO, Banque
  mondiale/WDI, UNICEF/SDMX, ONU/ODD et DHS, en plus de HDX et ReliefWeb.
- Archivage SHA-256 de la réponse distante brute conservé pour tous les nouveaux
  connecteurs ; normalisation des indicateurs et flux vers le modèle HDP.
- Onglet « Sources sanitaires » distinguant 7 API actives de 11 portails de
  référence avec accès, domaines, inscription et liens officiels.
- 36 tests unitaires, compilation Python et syntaxe JavaScript validés.

## 2.4.1 — 14 août 2026

- Passerelle locale `github-api` vers l'API REST GitHub classique.
- Lectures de dépôt, branches, commits, issues, pull requests, releases,
  workflows, contenus et quotas.
- Création d'issues et déclenchement de workflows désactivés par défaut.
- Jeton conservé côté serveur et version REST configurable.

## 2.4.0 — 7 août 2026

- Présentation des téléchargements officiels sous forme de liste par famille :
  COD-AB et COD-PS sont sélectionnables dans un même profil de projet.
- COD-CS reste visible mais désactivé tant que son registre vérifié embarqué ne
  contient aucun jeu ; COD-HP est visible comme famille retirée par OCHA.
- Remplacement du périmètre hiérarchique libre par une liste de pays ou zones
  appartenant simultanément à ONU M49 et à tous les catalogues HDX sélectionnés.
- Vérification réelle du 7 août 2026 : 163 pays/zones COD-AB, 146 COD-PS et
  143 options dans leur intersection ; Soudan admissible aux deux, Algérie au
  seul COD-AB.
- Téléchargement atomique par ensemble de familles : si une famille devient
  absente, la preuve CKAN est archivée mais aucun sous-ensemble n'est téléchargé.
- Ajout de `cod_families` aux profils et de `cod_family` à la provenance locale ;
  migration sûre des anciens profils pays, suspension explicite des profils
  monde/région jusqu'au choix dans la nouvelle liste.
- Ajout des routes `/api/cod/families` et `/api/cod/availability`, avec cache HDX
  de 30 minutes et registre COD-CS versionné.
- Validation : 29 tests unitaires, contrôle JavaScript et recette catalogue HDX
  en direct sur COD-AB/COD-PS.

## 2.3.2 — 7 août 2026

- Correction de la découverte HDX : le catalogue est interrogé par identifiant
  canonique `cod-ab-*` et niveau COD, puis chaque résultat est contrôlé contre
  son groupe ISO3 ONU M49.
- Compatibilité avec les réponses CKAN qui indexent la série officielle mais
  n'exposent plus `dataseries_name` dans le JSON retourné.
- Invalidation du dernier statut, de la dernière erreur et de l'acquisition
  affichés lorsqu'un profil change de périmètre M49, de politique ou de format.
- Affichage explicite « synchronisation requise » et échéance immédiate lorsque
  le téléchargement automatique est actif sur un profil modifié.
- Régressions vérifiées sur les COD-AB officiels du Soudan (`M49 729`, `SDN`)
  et de l'Algérie (`M49 012`, `DZA`).

## 2.3.1 — 7 août 2026

- Remplacement de l'échelle opérationnelle « terrain → monde » par la nomenclature
  officielle ONU M49 embarquée et hiérarchisée.
- Suppression de l'identifiant HDX libre dans le module géographique.
- Limitation stricte aux jeux OCHA/HDX de la série officielle
  `COD - Subnational Administrative Boundaries`, marqués `cod-enhanced` ou
  `cod-standard`.
- Ajout des politiques « amélioré uniquement » et « amélioré avec standard en
  repli ».
- Archivage de la provenance : code M49, ISO3, niveau COD, éditeur, licence et
  date des métadonnées.
- Migration sûre : les anciens profils monde deviennent M49 `001`; les profils
  plus étroits sont suspendus jusqu'au choix explicite d'un territoire M49.
- Correction de la limite d'acquisition : les fichiers déjà présents ne
  consomment plus le quota et les ressources restantes sont reportées, pas
  assimilées à des échecs.

## 2.3.0 — 7 août 2026

- Paramètres GitHub par projet et création de dépôt.
- Profil géographique HDX, synchronisation planifiée et téléchargement local.
- Correctif Windows de configuration sûre de `GITHUB_TOKEN`.

Les journaux détaillés historiques restent également inclus dans leurs archives
de remise respectives sous `dist/`.
