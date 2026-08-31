# ReliefWeb — journal des cycles de qualification

## Cycle 1 — documentation / descriptor
État : IMPLEMENTED, deterministic qualification pending CI. Ajout du prompt canonique, invariants HDP, ProviderDescriptor et limites documentées. Les presets sont spécifiques au type de contenu ; la documentation officielle ne présente pas `references` dans les tables de champs comme un contenu ordinaire. Aucun schéma de champs `references` n'est inventé.

## Cycle 2 — query / client / configuration
État : PARTIAL. Le noyau `reliefweb_v2.py` couvre query, filtres récursifs, facettes, pagination, profiles/presets, projection fields et GET/POST. Nouveau ProviderService ajouté avec résolution default/global/project et classification 403. L'ancien exécuteur sémantique `/reports` reste à migrer avant qualification complète.

## Cycle 3 — storage / provenance / drift
État : TODO. Réutiliser les settings HDP globaux/projet ; ajouter provider_* uniquement là où nécessaire. RawArtifact immuable et normalisation versionnée obligatoires. `appname` doit être public et influencer la provenance effective, sans contaminer la gestion des secrets.

## Cycle 4 — UI / clients / jobs
État : TODO. UI hybride Simple/Avancé/Expert alimentée par descriptor ; clients R/Python via API HDP ; exhaustive acquisition via jobs communs.

## Cycle 5 — intégration / live / build
État : BLOCKED. Le test live GitHub Actions du 2026-08-31 a reçu HTTP 403 pour `appname=HDP_plateforme` dès `/v2/reports?limit=1&profile=full`. Ce résultat est conservé comme blocage fournisseur/configuration et ne sera pas neutralisé pour rendre la CI verte. L'installateur V7 est donc non qualifié sur ce head.

## Règle de sortie
FINALIZED interdit tant que le 403 n'est pas résolu et que les gates G1..G4 ne sont pas verts. La qualification documentaire et déterministe peut progresser indépendamment, mais doit rester distinguée de la qualification live.
