# DHS — rapport final de qualification HDP V7

## Référence

Périmètre qualifié sur le commit de code `0f8146bca6d78f218458053b6187f68a89cf7603`, PR #21. Procédure : `dev_connecteurs` v1.0.

## Architecture et sécurité sémantique

Le connecteur DHS possède un package fournisseur dédié avec descripteur, service de référence, API/UI native et délégation du routeur sémantique. La géographie n'est jamais convertie directement d'ISO3 vers `countryIds` : HDP conserve `iso3_lookup`, interroge le catalogue officiel DHS `countries`, exige une correspondance unique `ISO3_countryCode`, puis utilise le `DHS_countryCode` réellement retourné. Une absence ou ambiguïté de mapping échoue explicitement.

La complétude des recherches bornées reste `bounded`; une réponse vide bornée ne prouve jamais l'absence globale de données.

## Qualification déterministe

Workflow `HDP V7 six connectors qualification` run `33430824449` : SUCCESS. Les 10 cycles ont été réexécutés réellement. Pour DHS : 8 contrôles × 10 cycles = 80 contrôles PASS, 0 FAIL. Les contrôles couvrent preuves officielles, contrat d'opération, rejet des paramètres inconnus, dette explicite, route sémantique, complétude bornée, non-contamination de `project_id` et résolution géographique dynamique sans substitution de `countryIds`.

Le même workflow a exécuté la régression source complète avec succès, le contrat client Python spécialisé avec succès et le job R avec succès. Le workflow global V7 run `33430824311`, le full application audit run `33430824282`, le full qualification run `33430824401`, le parameter audit run `33430824484`, le Windows installer run `33430824116` et la validation run `33430824198` sont SUCCESS sur le même commit.

## Qualification live

Sentinelle exécutée le `2026-08-31T19:29:30Z` : GET `https://api.dhsprogram.com/rest/dhs/countries?f=json&page=1&perpage=5`, HTTP 200, 5 éléments normalisés, aucune erreur. La requête native et le statut HTTP sont conservés dans l'artefact `HDP-V7-six-connectors-live` ID `9772516526`, digest ZIP `sha256:4cacf3d31f5c0a590f95e44e89bccf701048445c1a2ed4c9d47cbcaf7d5d39b1`.

Artefact déterministe : `HDP-V7-six-connectors-deterministic` ID `9772525901`, digest `sha256:9d6459aefa41182cb6b05b760fd4269870f8f0d5a8dce50ed2ecdbf5905765f9`.

## Clients, UI et provenance

Les opérations qualifiées sont accessibles par API native HDP, interface Simple/Avancé/Expert et clients reproductibles Python/R. Les appels spécialisés conservent requête catalogue, ligne de mapping utilisée, requête de données, paramètres sémantiques natifs et payload brut/référence nécessaires à la provenance.

## Limites

L'API DHS publie ses propres codes pays ; HDP ne les dérive jamais depuis ISO3 sans interrogation du catalogue. Les recherches restent bornées selon les paramètres et limites du fournisseur. L'indisponibilité fournisseur, l'authentification, un changement de contrat ou un mapping non unique restent des erreurs/BLOCKED, jamais un faux zéro.

## Verdict

**IMPLÉMENTÉ ET QUALIFIÉ — QUALIFIÉ POUR TEST UTILISATEUR** pour le périmètre DHS V7 documenté et testé. La qualification release de HDP reste distincte et requiert encore l'UAT Windows sur machine cible.
