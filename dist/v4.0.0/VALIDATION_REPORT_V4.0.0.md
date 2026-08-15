# Rapport de validation - HDP 4.0.0

Version publiée sur la branche GitHub `main`. L’installateur a été produit au
commit `9188db4a772d6c540dab33a091cf4bd6d7ba5780`.

## Contrôles réussis dans l’environnement de construction

- 90 tests Python `unittest` ;
- compilation des modules API, passerelle, tests et outils ;
- analyse de tous les scripts JavaScript inline ;
- contrôle statique réseau, runners, SQL, import, SSRF et `.env` ;
- SBOM CycloneDX 1.5 reproductible ;
- recettes testées sur filtre, taux, déduplication et agrégation ;
- parseurs testés sur les dix contrats de connecteurs ;
- payload et archives déterministes avec inventaire et SHA-256.
- workflow Linux `HDP validation` réussi sur GitHub Actions ;
- compilation MSVC Windows réussie, métadonnées 4.0.0 contrôlées ;
- exécutable vérifié PE32+ GUI x64 avec ASLR, NX et haute entropie ;
- artefact GitHub Actions et empreinte SHA-256 récupérés puis contrôlés.

## Contrôles non attestés

- démarrage Compose/PostGIS : Docker indisponible ;
- appels directs aux API : réseau de test non ouvert aux domaines ;
- installation/mise à niveau sur Windows 10/11 et Docker Desktop ;
- signature Authenticode : certificat non fourni ;
- audit indépendant et choix de licence : décisions externes.

## Décision

Le code, le payload portable, l’installateur natif compilé, les tests, scripts
de construction, documentation et manifestes 4.0.0 sont livrables. L’EXE peut
être annoncé comme compilé et contrôlé statiquement, mais pas comme signé ni
recetté manuellement sur Windows 10/11. L’archive historique 3.0.0 reste
inchangée.
