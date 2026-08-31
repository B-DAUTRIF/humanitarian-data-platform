# UN SDG — rapport final de qualification HDP V7

## Référence

Périmètre qualifié sur le commit de code `0f8146bca6d78f218458053b6187f68a89cf7603`, PR #21, procédure `dev_connecteurs` v1.0.

## Architecture et nomenclature

Le connecteur UN SDG possède un package fournisseur dédié, un service de référence, une API/UI native et une délégation du routeur sémantique. Les zones sont traduites à partir de la nomenclature ONU vérifiée : Rwanda est résolu par HDP en M49 `646`, puis transmis comme `areaCode=646`. Les périodes sont traduites en années explicites. Les recherches thématiques utilisent le catalogue de séries/indicateurs sans inventer de code série.

L'auditeur a été corrigé afin qu'une opération officiellement sans paramètre, telle que `list_indicators`, soit reconnue comme un contrat déclaré valide au lieu d'échouer parce que sa liste de paramètres est vide.

## Qualification déterministe

Workflow six connecteurs `33430824449` : SUCCESS. UN SDG : 8 contrôles × 10 réexécutions = 80/80 PASS, 0 FAIL. Le contrôle spécifique confirme `Rwanda → M49 646 → areaCode=646`. La régression source complète, le client Python spécialisé et le job R ont également réussi.

Les workflows full application audit `33430824282`, global 10-cycle `33430824311`, full qualification `33430824401`, parameter audit `33430824484`, Windows `33430824116` et validation `33430824198` sont SUCCESS sur le commit de qualification.

## Qualification live

Sentinelle : GET `https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List`, HTTP 200, 251 éléments observés et normalisés, sans erreur. Exécution le `2026-08-31T19:29:41Z`.

Preuves : artefact live `9772516526`, digest `sha256:4cacf3d31f5c0a590f95e44e89bccf701048445c1a2ed4c9d47cbcaf7d5d39b1`; artefact déterministe `9772525901`, digest `sha256:9d6459aefa41182cb6b05b760fd4269870f8f0d5a8dce50ed2ecdbf5905765f9`.

## Limites et provenance

Les codes de séries et dimensions sont issus des contrats/catalogues fournisseurs et non reconstruits par heuristique. Les recherches bornées restent non conclusives pour un zéro global. Requête native, paramètres traduits, contrat fournisseur, réponse/référence et normalisation sont conservés pour la provenance.

## Verdict

**IMPLÉMENTÉ ET QUALIFIÉ — QUALIFIÉ POUR TEST UTILISATEUR** pour le périmètre UN SDG V7 testé. La qualification release de HDP demeure soumise à l'UAT Windows sur machine cible.
