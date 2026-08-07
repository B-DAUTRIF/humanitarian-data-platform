# Dépannage

## Diagnostic borné

1. Double-cliquez sur `HDP_Diagnostic_v2.3.cmd`.
2. Attendez la fin ; chaque commande externe est limitée à 15 secondes.
3. Récupérez `HDP_Debug_v2.3_*.log` sur le Bureau.
4. Relisez et masquez toute information personnelle avant partage.

## Problèmes courants

| Symptôme | Cause probable | Action |
|---|---|---|
| Docker ne répond pas | Premier démarrage, WSL ou conditions Docker en attente | Ouvrir Docker Desktop, terminer son assistant, puis relancer |
| Port 8080 refusé | Port occupé ou réservé | Lire `HDP_PORT` dans `.env`; l'installateur choisit `18080–18279` |
| ReliefWeb retourne 503 | `RELIEFWEB_APPNAME` absent | Obtenir un appname pré-approuvé, l'ajouter à `.env`, redémarrer |
| Création GitHub indisponible | `GITHUB_TOKEN` absent ou application non redémarrée | Ajouter un jeton à droits minimaux dans `.env`, puis redémarrer l'API |
| Création GitHub refusée | dépôt existant ou droits compte/organisation insuffisants | Choisir un autre nom ou ajuster les permissions du jeton |
| Synchronisation géographique sans ressource | format choisi absent du jeu HDX | Vérifier le jeu sur HDX ou choisir un autre format |
| Ressource `failed` | URL, réseau, taille, redirection privée ou source distante | Lire l'erreur dans Données locales et ajuster les préférences |
| Ressource ignorée | Limite de quantité ou format non autorisé | Modifier les préférences du projet |
| Planification jamais exécutée | Suspendue ou planificateur arrêté | Vérifier le badge de santé, réactiver puis consulter les journaux API |
| Empreinte invalide | Fichier modifié après téléchargement | Ne pas utiliser le fichier ; relancer une acquisition |
| Fichier local absent | Déplacement ou suppression externe | La provenance reste en base ; relancer l'acquisition si nécessaire |

## Commandes utiles

Dans `%USERPROFILE%\HumanitarianDataPlatform` :

```powershell
docker compose ps --all
docker compose logs --no-color --tail 200 api db
docker compose up -d --build db api
```

N'utilisez pas `docker compose down -v`, **Clean/Purge data** ou **Reset to factory defaults** si les données doivent être conservées.
