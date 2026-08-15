# Rapport de validation - HDP 4.0.0

Branche `codex/finalize-hdp-v4`, issue de la photographie GitHub
`6eff2065fadc8070be398ecce7560c6d2db44084`.

## Contrôles réussis dans l’environnement de construction

- 90 tests Python `unittest` ;
- compilation des modules API, passerelle, tests et outils ;
- analyse de tous les scripts JavaScript inline ;
- contrôle statique réseau, runners, SQL, import, SSRF et `.env` ;
- SBOM CycloneDX 1.5 reproductible ;
- recettes testées sur filtre, taux, déduplication et agrégation ;
- parseurs testés sur les dix contrats de connecteurs ;
- payload et archives déterministes avec inventaire et SHA-256.

## Contrôles non attestés

- démarrage Compose/PostGIS : Docker indisponible ;
- appels directs aux API : réseau de test non ouvert aux domaines ;
- compilation PE32+ : aucun Zig/MinGW installé ;
- installation/mise à niveau sur Windows 10/11 et Docker Desktop ;
- signature Authenticode : certificat non fourni ;
- audit indépendant et choix de licence : décisions externes.

## Décision

Le code, le payload portable, les tests, scripts de construction, documentation
et manifestes 4.0.0 sont livrables. Aucun EXE 4.0.0 ne doit être annoncé comme
compilé ou validé. L’archive historique 3.0.0 reste inchangée.

