# WHO GHO — rapport final de qualification HDP V7

## Référence

Périmètre qualifié sur le commit de code `0f8146bca6d78f218458053b6187f68a89cf7603`, PR #21, procédure `dev_connecteurs` v1.0.

## Architecture

Le connecteur WHO GHO dispose d'un package fournisseur dédié, d'un service de référence, d'une API/UI native HDP et d'une délégation du routeur sémantique. Le normaliseur des indicateurs OData est désormais autonome et ne dépend plus de `app.main`; `IndicatorCode`, `IndicatorName` et la ligne native restent conservés pour la provenance.

Les opérations de catalogue/dimensions et les appels OData explicitement paramétrés sont exposés. Le routage observationnel générique géographie/temps reste volontairement bloqué : le contrat legacy GHO OData ne doit pas être extrapolé vers le contrat moderne WHO post-2025 sans requalification documentaire et technique.

## Qualification déterministe

Workflow six connecteurs `33430824449` : SUCCESS. WHO GHO : 8 contrôles × 10 cycles = 80/80 PASS sur le périmètre déclaré, avec contrôle explicite du blocage de dérive de contrat observationnel. Régression backend complète, client Python spécialisé et job R : SUCCESS.

Les workflows full application audit `33430824282`, global 10-cycle `33430824311`, full qualification `33430824401`, parameter audit `33430824484`, Windows `33430824116` et validation `33430824198` sont SUCCESS sur le commit de qualification.

## Qualification live

Sentinelle : GET `https://ghoapi.azureedge.net/api/Indicator?%24top=5&%24skip=0&%24format=json`, HTTP 200, 5 indicateurs normalisés, aucune erreur, le `2026-08-31T19:29:45Z`.

Preuves : artefact live `9772516526`, digest `sha256:4cacf3d31f5c0a590f95e44e89bccf701048445c1a2ed4c9d47cbcaf7d5d39b1`; artefact déterministe `9772525901`, digest `sha256:9d6459aefa41182cb6b05b760fd4269870f8f0d5a8dce50ed2ecdbf5905765f9`.

## Limites

La qualification prouve le catalogue legacy GHO et les opérations explicitement paramétrées couvertes par le service. Elle ne prouve pas que les dimensions ou filtres legacy sont interchangeables avec les APIs WHO modernes. Géographie et période en routage observationnel générique restent donc bloquées au lieu d'être devinées. Toute erreur de contrat/fournisseur demeure explicite et ne peut devenir `empty_valid`.

## Verdict

**PARTIELLEMENT IMPLÉMENTÉ — QUALIFIÉ POUR TEST UTILISATEUR sur le périmètre catalogue/OData legacy explicitement paramétré.** Le routage observationnel moderne doit être requalifié avant que le connecteur entier puisse devenir `IMPLÉMENTÉ ET QUALIFIÉ`. La release HDP reste soumise à l'UAT Windows cible.
