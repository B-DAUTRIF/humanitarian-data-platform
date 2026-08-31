# GDACS — rapport final de qualification HDP V7

## Référence

Périmètre qualifié sur le commit de code `0f8146bca6d78f218458053b6187f68a89cf7603`, PR #21, selon `dev_connecteurs` v1.0.

## Architecture

Le connecteur utilise un package GDACS dédié, un service de référence, une API/UI HDP native et la délégation sémantique vers ce service. Le normaliseur GDACS est autonome et ne dépend plus de `app.main`; la feature native est conservée dans `_native` avec type d'événement, niveau d'alerte, dates, pays/zone et URL.

Les filtres qualifiés portent sur la période, la liste des types d'événement et les niveaux d'alerte. HDP ne transforme pas arbitrairement une géographie canonique en filtre pays GDACS : tant qu'un mapping natif exact n'est pas vérifié, ce critère reste `blocked_missing_mapping`.

## Qualification déterministe

Workflow six connecteurs run `33430824449` : SUCCESS. GDACS a passé 8 contrôles sur chacun des 10 cycles, soit 80/80 PASS. Les invariants incluent preuves documentaires, contrat, rejet des paramètres inconnus, dette explicite, provenance de route, complétude bornée, non-contamination de `project_id` et interdiction de deviner un filtre géographique fournisseur.

La régression backend complète du workflow six connecteurs est SUCCESS. Les jobs Python spécialisé et R sont SUCCESS. Sont également SUCCESS sur le commit de qualification : full application audit `33430824282`, global 10-cycle audit `33430824311`, full qualification `33430824401`, parameter audit `33430824484`, Windows installer `33430824116` et validation `33430824198`.

## Qualification live

Sentinelle : GET `https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?fromdate=2026-08-17&todate=2026-08-31&alertlevel=green%3Borange%3Bred`, HTTP 200, 100 événements normalisés, aucune erreur. Exécution du `2026-08-31T19:29:31Z` au `19:29:41Z`.

Preuves : artefact live `9772516526`, digest `sha256:4cacf3d31f5c0a590f95e44e89bccf701048445c1a2ed4c9d47cbcaf7d5d39b1`; artefact déterministe `9772525901`, digest `sha256:9d6459aefa41182cb6b05b760fd4269870f8f0d5a8dce50ed2ecdbf5905765f9`.

## Limites

Le périmètre qualifié ne prétend pas disposer d'un filtre géographique natif par pays. Une recherche bornée ou filtrée localement ne peut pas conclure `empty_valid`. Toute erreur HTTP, timeout ou changement de contrat reste une erreur fournisseur explicite.

## Verdict

**IMPLÉMENTÉ ET QUALIFIÉ — QUALIFIÉ POUR TEST UTILISATEUR** pour la recherche événementielle GDACS qualifiée. Le filtrage géographique natif reste une capacité non qualifiée explicitement bloquée, sans affecter le statut du périmètre testé. La release HDP reste soumise à l'UAT Windows cible.
