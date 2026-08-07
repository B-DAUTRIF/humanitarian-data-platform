# Diagnostic, sauvegarde et dépannage

## Produire un diagnostic

1. Double-cliquez sur `HDP_Diagnostic_v1.5.cmd`.
2. Attendez la fin des contrôles, limités à 15 secondes chacun.
3. Récupérez `HDP_Debug_v1.5_*.log` sur le Bureau.
4. Relisez le fichier avant tout partage et n'y ajoutez jamais le contenu de `.env`.

Le diagnostic recense Windows, l'espace disque, les logiciels, WSL, Docker, les contextes, les ports en écoute, les services Compose et leurs journaux. Des lignes de code de sortie vides ou des caractères mal décodés peuvent être des défauts cosmétiques du script.

## Résolution des incidents courants

| Symptôme | Cause probable | Action |
|---|---|---|
| Docker ne répond pas | Premier démarrage, WSL ou conditions Docker | Ouvrir Docker Desktop, terminer son assistant et vérifier `wsl --version` |
| Arrêt après plusieurs minutes | Moteur Docker non prêt | Appliquer la mise à jour ou le redémarrage demandé, puis relancer HDP |
| Port 8080 refusé | Port occupé ou réservé | La v1.5 choisit `18080` à `18279` ; lire uniquement `HDP_PORT` dans `.env` |
| ReliefWeb renvoie 503 | Appname absent | Obtenir un appname pré-approuvé et le configurer |
| Une source renvoie 502 | Réseau, proxy ou API distante | Vérifier la connexion et réessayer plus tard |
| R indique `not_started` | Profil analytique non lancé | Utiliser `start-hdp-with-r.cmd` ou réinstaller avec R |
| Disque presque plein | Images, cache ou données | Libérer de l'espace ou déplacer l'image disque Docker |
| Le navigateur ne s'ouvre pas | Association ou lancement bloqué | Lire `HDP_PORT` et ouvrir `http://localhost:<HDP_PORT>` |

## Critères d'un démarrage réussi

```text
api Up ... (healthy) 127.0.0.1:<HDP_PORT>->8080/tcp
db Up ... (healthy) 5432/tcp
GET /api/health HTTP/1.1 200 OK
```

Les messages PostgreSQL `enabling trust authentication`, `received fast shutdown request` ou `logical replication launcher exited` peuvent apparaître pendant l'initialisation contrôlée. Le message `database system is ready to accept connections`, les contrôles de santé et HTTP 200 sont les signaux prioritaires.

## Sauvegarder

Sauvegardez :

- le dossier `data` ;
- un export SQL de la base `acquisitions` ;
- `.env` dans un emplacement protégé ;
- l'installateur et les sources de la version utilisée.

Depuis le dossier installé, dans `cmd.exe` :

```bat
docker compose exec -T db pg_dump -U humanitarian -d humanitarian --no-owner --no-privileges > humanitarian_backup.sql
```

## Restaurer

Une restauration peut écraser ou fusionner des objets SQL. Testez-la d'abord sur une copie et conservez une sauvegarde du volume actuel. Pour une base vide :

```bat
docker compose exec -T db psql -U humanitarian -d humanitarian < humanitarian_backup.sql
```

## Actions destructives à éviter

N'utilisez jamais les actions suivantes comme première mesure de dépannage :

- `docker compose --profile analytics down -v` ;
- **Clean/Purge data** dans Docker Desktop ;
- **Reset to factory defaults**.

Elles peuvent supprimer le volume PostgreSQL ou d'autres données. La commande `down -v` n'est appropriée que pour une suppression complète explicitement souhaitée, après vérification d'une sauvegarde.
