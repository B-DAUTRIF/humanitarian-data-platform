# HDP 4.0.0 — point de reprise final

## Identité du chantier

- date du point : 2026-08-15 15:24 CEST ;
- dépôt : `B-DAUTRIF/humanitarian-data-platform` ;
- branche distante : `codex/finalize-hdp-v4` ;
- base GitHub : `6eff2065fadc8070be398ecce7560c6d2db44084` ;
- base locale importée : `aa699c0`, tag `local-baseline-6eff2065` ;
- gel fonctionnel local : `0024f5b` ;
- conditionnement reproductible : `c49f18646fe5c6d250d818f61e2a9d35b747bc62` ;
- version cible : 4.0.0.

## État vérifié — checkpoint fonctionnel 1

- le dépôt contient le code complet de HDP 3.0.0 et ses livrables historiques ;
- `python -m unittest discover -s source/tests -v` : **82/82 réussis** ;
- `python -m compileall -q source/payload/api/app source/tests` : **réussi** ;
- extraction du JavaScript inline puis `node --check` : **réussi** ;
- l'application expose sept connecteurs actifs et des contrats JSON Schema
  propres à chacun ;
- l'interface dispose déjà des vues Recherche, Sources, Paramètres, Projets,
  Données locales, RSS, Chronologie, Carte, Scripts et Planifications ;
- HDP-028 à HDP-035 disposent maintenant d'un premier parcours intégré :
  recherche multi-API, champs spécifiques, imports, carte, périodicité,
  planification par fichier, accueil et SQL en lecture seule ;
- trois migrations 4.0.0 ajoutent recherche fédérée, lignée, bibliothèque locale,
  planifications par ressource et vues SQL limitées au projet ;
- les connecteurs prioritaires, le modèle normalisé/dérivé, les recettes guidées,
  les fichiers massifs et la qualification finale restent à terminer.

## État vérifié — checkpoint fonctionnel 2

- le registre compte dix connecteurs actifs ;
- HDX HAPI, UNHCR et GDACS possèdent chacun un schéma de paramètres, une
  prévisualisation expurgée et un parseur normalisé testé ;
- IOM DTM et WHO DON sont explicitement référencés sans simuler une API ou
  contourner leurs modalités d’accès ;
- `python -m unittest discover -s source/tests -v` : **85/85 réussis** ;
- `python -m compileall -q source/payload/api/app source/tests` : **réussi**.

## État vérifié — checkpoint fonctionnel 3

- moteur guidé CSV/TSV et scripts reproductibles Python/R intégrés ;
- profilage en flux, déduplication et agrégation bornées, lignée dérivée ;
- import atomique avec validation de contenu et archives passives ;
- carte multi-couches avec vérification d’intégrité ;
- `python -m unittest discover -s source/tests -v` : **90/90 réussis** ;
- analyse syntaxique du JavaScript : **réussie**.

## État vérifié — checkpoint de gel 4

- numéros de version applicatifs et contrats alignés sur **4.0.0** ;
- workflow CI, SBOM CycloneDX, contrôles de sécurité statiques et contrôle des
  scripts JavaScript ajoutés ;
- sauvegarde/restauration documentée et scripts PowerShell embarqués ;
- prompt global, guide utilisateur, installation, référence API, matrice des
  sources, sécurité, limites et rapport de validation synchronisés ;
- notice PDF de **27 pages** rendue sans page vide ni tiret Unicode résiduel ;
- **90/90 tests Python réussis**, compilation Python réussie ;
- runner C17 compilé avec `-Wall -Wextra -Werror` ;
- payload embarqué régénéré et contrôle de reconstruction réussi ;
- `compose.yaml` analysé comme YAML valide avec **6 services** ;
- script de conditionnement v4 déterministe ajouté ; il refuse de modifier un
  répertoire `dist/v4.0.0` déjà gelé.

## Prochaine action exacte en cas de reprise

1. vérifier `git status --short` ;
2. si `dist/v4.0.0` est absent, exécuter
   `python3 tools/package_v4_release.py` ;
3. vérifier les trois ZIP et les empreintes, puis consigner le SHA-256 de
   l'archive globale ;
4. ne jamais modifier les archives `dist/v3.0.0` et antérieures ;
5. publier la branche uniquement avec le flux GitHub autorisé et garder le
   dépôt privé tant que la licence HDP n'est pas choisie.

## Commandes de vérification

```bash
git status --short
python -m unittest discover -s source/tests -v
python -m compileall -q source/payload/api/app source/payload/github-api source/tests tools
node tools/check_inline_javascript.mjs source/payload/api/static/index.html
python tools/security_static_checks.py
gcc -std=c17 -O2 -Wall -Wextra -Werror source/payload/runner/runner.c -o /tmp/hdp-runner-v4
```

## Fichiers de conduite

- `docs/FINALIZATION_PLAN_V4.md` : lots et critères d'acceptation ;
- `HDP_v4.0.0_Point_de_reprise.md` : reprise technique courante ;
- `LOG-Huma_2026_15_08_14-23-11_005.log` : journal de ce point ;
- TODO durable : `TODO_Mises_a_jour_HDP.md`, mise à jour pour le gel 4.0.0 et
  copiée dans l'archive globale.

## Blocages externes connus

- publication du code : le flux GitHub autorisé exige le client `gh`, absent de
  l'environnement courant ; la branche distante existe mais les commits de
  code locaux ne sont pas encore publiés ;
- machine Windows 10/11 réelle avec Docker Desktop non disponible ici ;
- certificat Authenticode non fourni ;
- licence du logiciel non choisie ;
- audit de sécurité indépendant non mandaté.
