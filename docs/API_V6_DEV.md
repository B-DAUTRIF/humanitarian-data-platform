# Référence API HDP 6.0.0

Cette référence décrit le périmètre API de la version finale V6.0.0. Elle complète la [référence V5](API_V5.md) : les routes V5
compatibles restent disponibles, mais aucune route V6 ne doit être interprétée
comme une qualification du déploiement Internet.

## Sécurité et conventions

- Toutes les routes, sauf santé, fichiers statiques et amorçage local, exigent
  une session HDP valide.
- Toute mutation exige `X-HDP-CSRF: 1` et une origine autorisée.
- Les identifiants de projet et d'objet sont des UUID.
- Les réponses d'erreur FastAPI utilisent `detail`; les messages sont bornés et
  ne doivent contenir ni secret ni URL signée complète.
- La définition OpenAPI servie par l'application (`/openapi.json` et `/docs`)
  reste la source exécutable canonique.

## Routes V6

Le jalon compte 59 chemins V6 et 66 couples méthode/chemin.

| Méthode | Route | Domaine |
|---|---|---|
| `POST` | `/api/v6/action-worker/run-once` | Exécuter au plus une demande d'action interne |
| `POST` | `/api/v6/actions/{request_id}/cancel` | Demander l'annulation d'une action |
| `POST` | `/api/v6/actions/{request_id}/decision` | Approuver ou rejeter une action contrôlée |
| `GET`, `POST` | `/api/v6/backups` | Lister ou créer une sauvegarde bornée |
| `GET` | `/api/v6/backups/{backup_id}/download` | Télécharger un paquet vérifié |
| `POST` | `/api/v6/backups/{backup_id}/prevalidate` | Prévalider sans restaurer |
| `POST` | `/api/v6/backups/{backup_id}/restore/temporary` | Restaurer dans une base temporaire neuve |
| `POST` | `/api/v6/cache/decision` | Calculer la décision de fraîcheur |
| `POST` | `/api/v6/cache/key` | Construire une clé de cache sans secret |
| `GET` | `/api/v6/catalog` | Consulter le catalogue central |
| `POST` | `/api/v6/connectors/capabilities/validate` | Valider une matrice de capacités |
| `POST` | `/api/v6/connectors/contracts/diff` | Comparer deux contrats |
| `POST` | `/api/v6/connectors/contracts/validate` | Valider un contrat d'endpoint |
| `GET` | `/api/v6/connectors/schema` | Lire le schéma commun des connecteurs |
| `POST` | `/api/v6/data-jobs/{job_id}/cancel` | Annuler un travail de données |
| `POST` | `/api/v6/data-worker/run-once` | Exécuter au plus un travail de données |
| `GET` | `/api/v6/mail/attachments/{attachment_id}/download` | Télécharger une pièce jointe confinée |
| `POST` | `/api/v6/mail/import-eml` | Importer manuellement un message EML public |
| `GET` | `/api/v6/mail/messages` | Lister les messages importés |
| `GET` | `/api/v6/mail/messages/{message_id}` | Lire un message et son inventaire |
| `POST` | `/api/v6/mail/messages/{message_id}/projects/{project_id}` | Rattacher un message à un projet |
| `GET` | `/api/v6/projects/{project_id}/actions` | Suivre décisions, tentatives et effets |
| `GET` | `/api/v6/projects/{project_id}/cache` | Lister le cache référencé par un projet |
| `POST` | `/api/v6/projects/{project_id}/cache/materialize` | Publier atomiquement un artefact de cache |
| `POST` | `/api/v6/projects/{project_id}/cache/{cache_entry_id}/revalidate` | Consigner une revalidation HTTP |
| `GET` | `/api/v6/projects/{project_id}/catalog-schedules` | Lister les mises à jour de catalogue |
| `POST` | `/api/v6/projects/{project_id}/catalog/import` | Importer métadonnées brutes et lignées |
| `GET` | `/api/v6/projects/{project_id}/data-jobs` | Suivre les résultats par source |
| `GET`, `PUT` | `/api/v6/projects/{project_id}/data-policy` | Lire ou définir la politique de fraîcheur |
| `POST` | `/api/v6/projects/{project_id}/rss/sources/{feed_source_id}/subscriptions` | Abonner le projet à un flux approuvé |
| `GET`, `POST` | `/api/v6/projects/{project_id}/rules` | Lister ou créer les règles du projet |
| `POST` | `/api/v6/projects/{project_id}/rules/migrate-legacy` | Prévisualiser ou confirmer le basculement transactionnel des règles V5 |
| `POST` | `/api/v6/projects/{project_id}/rules/{definition_id}/evaluate` | Évaluer une version de règle |
| `POST` | `/api/v6/projects/{project_id}/rules/{definition_id}/inheritance` | Décider une adoption ou surcharge |
| `PUT` | `/api/v6/projects/{project_id}/sources/{source_id}/catalog-schedule` | Configurer une mise à jour de catalogue |
| `PUT` | `/api/v6/projects/{project_id}/sources/{source_id}/endpoints/{endpoint_uuid}` | Configurer un endpoint pour un projet |
| `POST` | `/api/v6/projects/{project_id}/sources/{source_id}/equivalents/{capability}/materialize` | Produire un équivalent fonctionnel déclaré |
| `GET` | `/api/v6/projects/{project_id}/timeline` | Lire la chronologie projet |
| `GET`, `POST` | `/api/v6/rss/candidates` | Lister ou proposer un flux sans l'activer |
| `POST` | `/api/v6/rss/candidates/{feed_source_id}/decision` | Approuver, suspendre ou rejeter un flux |
| `POST` | `/api/v6/rss/candidates/{feed_source_id}/preview` | Contrôler réseau et parseur avant décision |
| `GET` | `/api/v6/rss/inventory-scope` | Lire le périmètre versionné de veille |
| `GET` | `/api/v6/rule-schema` | Lire le contrat des arbres ET/OU |
| `POST` | `/api/v6/rules/global` | Créer une règle globale versionnée |
| `POST` | `/api/v6/rules/simulate` | Simuler sans produire d'action |
| `POST` | `/api/v6/rules/validate` | Valider et hacher un arbre |
| `POST` | `/api/v6/rules/{definition_id}/versions` | Proposer une nouvelle version immuable |
| `GET` | `/api/v6/sources/{source_id}/configuration` | Lire la configuration expurgée |
| `POST` | `/api/v6/sources/{source_id}/contracts` | Importer un lot de contrats versionné |
| `GET` | `/api/v6/sources/{source_id}/endpoints` | Lister les endpoints inventoriés |
| `GET` | `/api/v6/sources/{source_id}/endpoints/{endpoint_uuid}` | Lire le détail d'un endpoint |
| `POST` | `/api/v6/sources/{source_id}/endpoints/{endpoint_uuid}/state` | Faire progresser ou suspendre un endpoint |
| `POST` | `/api/v6/sources/{source_id}/openapi/inventory` | Inventorier une définition OpenAPI locale |
| `GET`, `POST` | `/api/v6/spip/connections` | Lister ou créer une connexion SPIP minimale |
| `POST` | `/api/v6/spip/connections/{connection_id}/revoke` | Révoquer une connexion SPIP |
| `GET`, `POST` | `/api/v6/spip/publications` | Lister ou préparer un brouillon public |
| `GET`, `PATCH` | `/api/v6/spip/publications/{publication_id}` | Lire ou modifier un brouillon non publié |
| `POST` | `/api/v6/spip/publications/{publication_id}/decision` | Valider ou retirer une publication |
| `GET` | `/api/v6/timeline` | Lire la chronologie globale |

## Limites de qualification

Les travailleurs, restaurations temporaires et contrôles de contrat sont
testés sur PostgreSQL 16. Les appels réels aux connecteurs, le runtime SPIP
derrière HTTPS, la réception réseau des mails et la recette Windows/Docker
restent des portes distinctes : leur présence dans l'API ne les qualifie pas.
