# Dépannage

## Diagnostic borné

1. Double-cliquez sur `HDP_Diagnostic_v3.0.0.cmd`.
2. Attendez la fin ; chaque commande externe est limitée à 15 secondes.
3. Récupérez `HDP_Debug_v3.0.0_*.log` sur le Bureau.
4. Relisez et masquez toute information personnelle avant partage.

## Problèmes courants

| Symptôme | Cause probable | Action |
|---|---|---|
| Docker ne répond pas | Premier démarrage, WSL ou conditions Docker en attente | Ouvrir Docker Desktop, terminer son assistant, puis relancer |
| Port 8080 refusé | Port occupé ou réservé | Lire `HDP_PORT` dans `.env`; l'installateur choisit `18080–18279` |
| ReliefWeb retourne 503 | `RELIEFWEB_APPNAME` absent | Obtenir un appname pré-approuvé, l'ajouter à `.env`, redémarrer |
| Création GitHub indisponible | `GITHUB_TOKEN` absent ou conteneur API créé avant la modification de `.env` | Double-cliquer sur [`HDP_Configurer_GitHub_v3.0.0.cmd`](../../../dist/v3.0.0/HDP_Configurer_GitHub_v3.0.0.cmd), saisir le jeton dans l'invite masquée et attendre la vérification |
| Source sanitaire retourne 502 | API tierce indisponible, quota, changement de schéma ou délai dépassé | Ouvrir le lien Documentation dans « Sources sanitaires », réessayer plus tard et conserver l'erreur exacte |
| Portail sanitaire non proposé dans Recherche | entrée classée « Référence » | Utiliser le lien Portail ; HDP n'affirme pas une API publique stable pour cette source |
| Création GitHub refusée | dépôt existant ou droits compte/organisation insuffisants | Choisir un autre nom ou ajuster les permissions du jeton |
| `migration_required` | ancien profil monde/région non représentable dans la liste commune | Choisir un pays ou une zone ONU M49 × HDX, puis enregistrer |
| Liste géographique plus courte | plusieurs familles sélectionnées | La liste est leur intersection ; retirer explicitement une famille ou choisir une option commune |
| Algérie absente avec COD-PS | aucun `cod-ps-dza` canonique vérifié au 7 août 2026 | Sélectionner COD-AB seul ou un autre pays commun ; ne pas forcer un jeu non officiel |
| `no_official_dataset` | une famille sélectionnée a disparu du catalogue pour ce pays | Actualiser la liste, changer de pays ou retirer explicitement la famille |
| Nouveau périmètre avec l'erreur de l'ancien pays | installation 2.3.1 conservant le dernier statut | Mettre à niveau vers 2.4.0, enregistrer le profil puis synchroniser ; le statut devient d'abord « synchronisation requise » |
| Soudan ou Algérie indiqué sans COD-AB | filtre 2.3.1 exigeant `dataseries_name`, absent du JSON CKAN actuel | Mettre à niveau vers 2.4.0 et relancer la synchronisation |
| `no_matching_resource` | format COD-AB absent ou aucune ressource CSV/XLSX COD-PS | Changer le format COD-AB ou vérifier la publication officielle ; ne pas substituer un jeu arbitraire |
| Ressources `deferred` | limite de quantité atteinte | Attendre le prochain passage ou augmenter prudemment la limite du projet |
| Ressource `failed` | URL, réseau, taille, redirection privée ou source distante | Lire l'erreur dans Données locales et ajuster les préférences |
| Ressource ignorée | Limite de quantité ou format non autorisé | Modifier les préférences du projet |
| Planification jamais exécutée | Suspendue ou planificateur arrêté | Vérifier le badge de santé, réactiver puis consulter les journaux API |
| Runner Python indisponible | `runner-python` absent ou encore en construction | Exécuter `docker compose up -d --build runner-python api`, puis vérifier `/api/health` |
| Runner R indisponible | Profil analytique non démarré | Utiliser `start-hdp-with-r.cmd` ou `docker compose --profile analytics up -d --build runner-r r-service api` |
| Exécution refusée pour le réseau | Politique de sécurité 3.0.0 | Retirer l'activation réseau et l'allowlist ; seuls les jobs hors ligne sont admis |
| Flux RSS en échec | Réseau, redirection, taille ou XML distant invalide | Conserver l'erreur affichée, vérifier le flux officiel et réessayer plus tard |
| Carte sans fond | Comportement par défaut | Cliquer sur **Activer le fond OSM** uniquement si l'accès au service de tuiles est souhaité |
| Passerelle GitHub indisponible | Image absente ou port 8091 occupé | Vérifier `HDP_GITHUB_API_PORT`, puis exécuter `docker compose up -d --build github-api api` |
| Écriture GitHub refusée par la passerelle | Verrou serveur ou permission insuffisante | Vérifier `GITHUB_API_WRITE_ENABLED=true` et les droits minimaux du jeton sans jamais l'afficher |
| Empreinte invalide | Fichier modifié après téléchargement | Ne pas utiliser le fichier ; relancer une acquisition |
| Fichier local absent | Déplacement ou suppression externe | La provenance reste en base ; relancer l'acquisition si nécessaire |

## Commandes utiles

Dans `%USERPROFILE%\HumanitarianDataPlatform` :

```powershell
docker compose ps --all
docker compose logs --no-color --tail 200 api db runner-python github-api
docker compose up -d --build db runner-python github-api api
```

N'utilisez pas `docker compose down -v`, **Clean/Purge data** ou **Reset to factory defaults** si les données doivent être conservées.

## Correctif automatisé du jeton GitHub

Le fichier [`HDP_Configurer_GitHub_v3.0.0.cmd`](../../../dist/v3.0.0/HDP_Configurer_GitHub_v3.0.0.cmd) applique la procédure complète sous Windows :

1. il cible `%USERPROFILE%\HumanitarianDataPlatform` par défaut ;
2. il demande le jeton dans une saisie masquée et met à jour uniquement la clé `GITHUB_TOKEN` de `.env` ;
3. il exécute `docker compose up -d --no-deps --force-recreate api` sans supprimer les volumes ni recréer la base ;
4. il vérifie dans le conteneur que la variable est non vide, sans l'afficher ;
5. il rouvre HDP sur le port défini par `HDP_PORT`.

Ne collez jamais le jeton dans un journal, une issue GitHub ou une conversation. Si GitHub refuse ensuite la création, vérifiez les permissions du jeton et l'autorisation de créer un dépôt pour le compte ou l'organisation choisis.
