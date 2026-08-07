# Migration de 1.5, 2.0 ou 2.3.x vers 2.4.0

## Garanties

La migration est déclenchée au démarrage et peut être rejouée. Elle ne supprime ni fichiers, ni volumes, ni lignes d'acquisition.

1. création des tables `projects`, `project_preferences`, `project_scripts`, `schedules`, `schedule_runs` et `local_resources` si elles sont absentes ;
2. ajout de `project_id` et `schedule_id` à `acquisitions` ;
3. création du « Projet par défaut » ;
4. rattachement des acquisitions sans projet à ce projet ;
5. activation de la contrainte `NOT NULL` sur `acquisitions.project_id`.
6. création idempotente de `project_github_settings` et `project_geodata_settings`, puis ajout d'une ligne par projet existant ;
7. ajout idempotent de `m49_scope_code`, `official_policy` et `migration_required` ;
8. ajout de `cod_families`, initialisé à `["cod-ab"]` pour les profils existants ;
9. conservation des profils déjà limités à un pays ou une zone M49 ;
10. suspension des profils monde/région et du téléchargement automatique jusqu'au choix explicite d'une option ONU M49 × HDX ;
11. ajout de `cod_family` à la provenance des ressources locales, sans réécriture des anciennes lignes.

Une ancienne ligne de ressource garde `cod_family = NULL` si elle précède 2.4.0 ;
son niveau COD et ses autres métadonnées restent intacts. Toute nouvelle
ressource officielle reçoit `cod-ab` ou `cod-ps`.

Les anciens fichiers restent à leur emplacement `data/raw/<source>`. Leur colonne `raw_path` n'est pas réécrite. Les nouvelles acquisitions utilisent `data/raw/<project_uuid>/<source>`.

## Sauvegarde recommandée

Avant une mise à niveau importante, arrêtez HDP et sauvegardez :

```text
%USERPROFILE%\HumanitarianDataPlatform\.env
%USERPROFILE%\HumanitarianDataPlatform\data
volume Docker humanitarian-data-platform_postgres_data
```

Ne partagez pas `.env`. Pour sauvegarder le volume PostgreSQL, utilisez une procédure Docker adaptée à votre environnement ; n'employez pas **Clean/Purge data** ni **Reset to factory defaults**.

## Retour à 1.5

La v1.5 ignore les nouvelles tables mais son ancienne définition de `acquisitions` ne connaît pas les nouvelles colonnes. Un retour applicatif sans restauration de sauvegarde n'est pas un scénario officiellement validé. Conservez une sauvegarde cohérente si un retour arrière est nécessaire.
