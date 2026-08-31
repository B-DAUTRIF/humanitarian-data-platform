# ReliefWeb V2 — décision d'architecture HDP

## Décision
ReliefWeb est le premier connecteur riche individualisé de HDP, mais ne devient pas le contrat universel des fournisseurs. Le contrat commun reste SearchIntent/QueryPlan/ProviderOperation/ProviderService/RawArtifact/NormalizedRecord. Les capacités ReliefWeb (Lucene, filtres récursifs, facettes, scopes, presets) restent dans son ProviderDescriptor.

## Cohérence globale
Les settings globaux/projet, jobs, provenance, cache de metadata, stockage brut, schéma drift et erreurs doivent être des services HDP partagés. Aucun service ReliefWeb parallèle n'est autorisé lorsqu'un service commun existe. Les autres connecteurs doivent continuer à fonctionner lorsqu'ils ne possèdent pas les capacités ReliefWeb.

## Configuration
`appname` est une configuration publique : default `HDP_plateforme`, global override, project override. Les secrets futurs sont typés séparément. Un appname rejeté devient `configuration_error` et n'est jamais confondu avec `empty_valid`.

## Données
Le payload natif est immuable et conservé par hash/référence avant normalisation. La normalisation est versionnée. L'objet HDP conserve l'identifiant, href, score et une référence vers l'objet natif.

## Performance
Recherche interactive bornée ; acquisition exhaustive via jobs HDP et pagination contrôlée ; metadata/taxonomies via cache générique ; analyse en aval R/Python. Le quota documenté ReliefWeb (1000 requêtes/jour) et le maximum de 1000 entrées/appel sont des métadonnées du descripteur, pas des constantes du Semantic Core.

## Qualification
Le connecteur ne peut être promu que si ses tests déterministes et live passent sans casser les gates globaux. Le 403 live observé pour `HDP_plateforme` est un bloqueur réel à résoudre auprès de ReliefWeb/configuration, pas un test à assouplir.
