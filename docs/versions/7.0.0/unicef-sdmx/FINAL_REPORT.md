# UNICEF SDMX — rapport final de qualification HDP V7

## Référence

Périmètre qualifié sur le commit de code `0f8146bca6d78f218458053b6187f68a89cf7603`, PR #21, procédure `dev_connecteurs` v1.0.

## Architecture

Le connecteur utilise un package UNICEF SDMX dédié, un service de référence, une API/UI native et une délégation du routeur sémantique. Le normaliseur de dataflows est autonome et ne dépend plus de `app.main`. Les structures natives et identifiants agence/dataflow/version restent disponibles dans `_native` et dans la provenance.

La découverte de dataflows est qualifiée. L'accès `get_data` demeure explicitement structuré autour de `agency`, `dataflow`, `version` et de la clé SDMX. HDP ne fabrique pas une clé de données à partir d'une géographie ou d'une période canonique : une traduction observationnelle exige la résolution dataflow → DSD → dimensions → codelists → clé SDMX. Sans cette preuve, le routeur sémantique reste `blocked_missing_mapping`.

## Qualification déterministe

Workflow six connecteurs `33430824449` : SUCCESS. UNICEF SDMX : 8 contrôles × 10 cycles = 80/80 PASS pour le périmètre déclaré, avec contrôle spécifique de non-invention de DSD/clé. Régression backend complète, import client Python spécialisé et job R : SUCCESS.

Les workflows full application audit `33430824282`, global 10-cycle `33430824311`, full qualification `33430824401`, parameter audit `33430824484`, Windows `33430824116` et validation `33430824198` sont SUCCESS sur le commit de qualification.

## Qualification live

Sentinelle : GET `https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/dataflow/all/all/latest/?format=sdmx-json&detail=allstubs&references=none`, HTTP 200, 53 dataflows normalisés, aucune erreur, le `2026-08-31T19:29:45Z`.

Preuves : artefact live `9772516526`, digest `sha256:4cacf3d31f5c0a590f95e44e89bccf701048445c1a2ed4c9d47cbcaf7d5d39b1`; artefact déterministe `9772525901`, digest `sha256:9d6459aefa41182cb6b05b760fd4269870f8f0d5a8dce50ed2ecdbf5905765f9`.

## Limites

La découverte de structure et les requêtes SDMX explicitement paramétrées sont opérationnelles. En revanche, la résolution sémantique générique géographie/temps vers une clé d'observation n'est pas qualifiée tant que les DSD et codelists propres au dataflow n'ont pas été résolus et versionnés. Ce blocage est volontaire et empêche une nomenclature inventée.

## Verdict

**PARTIELLEMENT IMPLÉMENTÉ — QUALIFIÉ POUR TEST UTILISATEUR sur le périmètre dataflow/SDMX explicitement paramétré.** La résolution sémantique observationnelle DSD-spécifique reste `BLOCKED_MISSING_MAPPING` et empêche de déclarer le connecteur entier `IMPLÉMENTÉ ET QUALIFIÉ`. La release HDP reste également soumise à l'UAT Windows cible.
