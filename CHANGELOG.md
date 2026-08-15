# Journal des versions

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
