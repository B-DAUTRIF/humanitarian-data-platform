# HDP 6.0.0 — clôture P1 / P2

Date de qualification : 2026-08-30

## P1 — fiabilité, maintenance et qualité de production

La V6 consolide et conserve les éléments P1 déjà qualifiés du socle V5 : CI, SBOM/dépendances, import local, périodicité, SQL PostgreSQL/PostGIS en lecture seule, parcours recherche→acquisition→traitement→export, contrat commun des connecteurs et modèle canonique/traçabilité.

Les travaux anciennement ouverts sont couverts par les modules désormais présents dans le socle :

- recherche fédérée multi-source : `app/federated_search.py` et tests `test_federated_search.py` ;
- bibliothèque locale et périodicité par ressource : `app/local_library.py`, modèles `ResourceRefreshSchedule*` et migrations associées ;
- carte et données locales : `app/map_utils.py` ;
- portefeuille humanitaire : `app/humanitarian_sources.py` ;
- sources santé/surveillance/dénominateurs : `app/health_sources.py` ;
- traitements reproductibles Python/R : `app/processing_recipes.py` et `test_processing_recipes.py` ;
- synchronisation GitHub V6 : `app/github_sync.py`, profil utilisateur/projet, audit, push/pull et prévention des conflits ;
- sécurité : limites Host/Origin/CSRF, validation des URL publiques, exécution isolée, contrôle des secrets par variables d'environnement ;
- installation Windows : build MSVC x64 et contrôle PE/imports/version dans `.github/workflows/windows-v6-full.yml`.

Les validations automatisables de production sont intégrées dans `.github/workflows/ci.yml` : tests Python, compilation, syntaxe JavaScript, contrat Compose, image R/spool, runner C17, reproductibilité du payload, contrôles statiques de sécurité et propreté du diff.

## P2 — ergonomie, performances et fonctions complémentaires

La V6 conserve les fonctions P2 déjà livrées et consolide : paramètres spécifiques des sources, accueil, export de données, fonctions projet, carte, traitements guidés et intégrations. Les contrôles de contrat des sources sont présents dans la suite de tests (`test_source_registry.py`, `test_federated_search.py`, tests des sources santé/humanitaires et contrats GitHub). La chaîne V6 ajoute également une qualification Windows reproductible et une livraison complète avec SHA-256.

Le catalogue V6 de clients programmatiques couvre 10 familles de sources, 440 opérations et l'inventaire fonctionnel de 2 057 paramètres. La politique reste lecture seule par défaut pour les opérations classées écriture/administration.

## Limites qui ne peuvent pas être auto-certifiées par le développement

Ces éléments ne sont pas déclarés « réalisés » artificiellement : audit de sécurité indépendant, test de charge indépendant, recette manuelle sur postes Windows 10/11 physiques et signature Authenticode avec certificat de confiance. Ils restent des qualifications externes et non des défauts bloquants du build automatisé, conformément à la politique utilisée pour la précédente release qualifiée.

Le package R client additionnel `HDPClientsR` est conservé comme composant développeur. Son dernier `R CMD check` distant a mis en évidence un défaut de transport du catalogue gzip dans GitHub ; ce défaut n'affecte ni le service R embarqué de HDP ni l'installateur Windows. Le catalogue complet et la version locale du client restent dans les livrables de développement jusqu'à requalification dédiée du package R.

## Gates de promotion V6

Pour la promotion de `main`, les gates automatisables requis sont :

1. `HDP validation` = success sur le commit candidat ;
2. `HDP V6 full Windows installer` = success sur le même commit ;
3. exécutable PE32+ GUI x86-64 produit avec table d'imports Windows et métadonnées 6.0.0 ;
4. archive complète et sommes SHA-256 produites ;
5. promotion de `main` uniquement en fast-forward, sans force push.
