# UNHCR — rapport final de qualification HDP V7

## Référence

Périmètre qualifié sur le commit de code `0f8146bca6d78f218458053b6187f68a89cf7603`, PR #21, procédure `dev_connecteurs` v1.0.

## Architecture et sémantique

Le connecteur UNHCR utilise un package fournisseur dédié, un service de référence, une API/UI native HDP et la délégation du routeur sémantique. Une géographie générique n'est jamais fusionnée silencieusement : HDP conserve deux rôles natifs distincts, `country of origin` et `country of asylum`, avec `cf_type=ISO`; les requêtes et rôles restent identifiables dans la provenance.

Les périodes sont traduites explicitement en `yearFrom`/`yearTo`. Les erreurs de mapping, de fournisseur ou de contrat ne sont jamais assimilées à un résultat vide valide.

## Qualification déterministe

Workflow six connecteurs run `33430824449` : SUCCESS. UNHCR : 8 contrôles × 10 cycles réels = 80/80 PASS, sans échec. Le contrôle fournisseur spécifique vérifie la séparation `[origin, asylum]`. La régression backend complète, le client Python spécialisé et le job R sont SUCCESS.

Les workflows full application audit `33430824282`, global 10-cycle `33430824311`, full qualification `33430824401`, parameter audit `33430824484`, Windows `33430824116` et validation `33430824198` sont SUCCESS sur le commit de qualification.

## Qualification live

Sentinelle : GET `https://api.unhcr.org/population/v1/countries/?limit=5&page=1`, HTTP 200, 5 éléments observés, aucune erreur, le `2026-08-31T19:29:45Z`.

Preuves : artefact live `9772516526`, digest `sha256:4cacf3d31f5c0a590f95e44e89bccf701048445c1a2ed4c9d47cbcaf7d5d39b1`; artefact déterministe `9772525901`, digest `sha256:9d6459aefa41182cb6b05b760fd4269870f8f0d5a8dce50ed2ecdbf5905765f9`.

## Limites

Le périmètre qualifié conserve les rôles de déplacement forcé au lieu de produire une agrégation implicite. Les pages bornées ne permettent pas de conclure à une absence globale de données. Les catalogues et codes fournisseurs restent l'autorité pour les valeurs natives.

## Verdict

**IMPLÉMENTÉ ET QUALIFIÉ — QUALIFIÉ POUR TEST UTILISATEUR** pour le périmètre UNHCR V7 testé. La qualification release HDP reste conditionnée à l'UAT Windows sur machine cible.
