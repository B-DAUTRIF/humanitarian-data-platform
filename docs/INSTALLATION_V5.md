# Installation HDP V5

## Windows x64

Prérequis : Windows 10/11 x64, Docker Desktop et Compose v2. Vérifier l’empreinte :

```powershell
Get-FileHash .\HumanitarianDataPlatform_Setup_Native_GUI_v5.0.1.exe -Algorithm SHA256
Get-Content .\HumanitarianDataPlatform_Setup_Native_GUI_v5.0.1.exe.sha256
```

L’EXE installe le payload, préserve les données existantes lors d’une mise à niveau et génère des secrets indépendants. Il ouvre une URL d’amorçage locale contenant le jeton une seule fois ; le serveur le transforme en cookie `HttpOnly`.

### Mise à niveau corrective depuis 5.0.0

La version 5.0.1 corrige l'initialisation du volume Docker `execution_spool`,
rend la présence de `plumber` obligatoire dès la construction de l'image R et
force l'encodage UTF-8 de l'interface native. Il suffit de relancer le nouvel
EXE sur le même dossier : `.env`, `data/` et le volume PostgreSQL sont
conservés. Ne lancez pas `docker compose down -v`, qui supprimerait les volumes.

En cas de diagnostic, les deux commandes non destructives utiles sont :

```powershell
docker compose -f "$env:LOCALAPPDATA\HumanitarianDataPlatform\compose.yaml" ps
docker compose -f "$env:LOCALAPPDATA\HumanitarianDataPlatform\compose.yaml" --profile analytics logs --tail 120
```

## Linux poste ou serveur

Prérequis : Docker Engine et Compose v2.

```bash
cd source/payload
./install-linux.sh workstation
# ou
./install-linux.sh server
```

En serveur, utiliser un tunnel SSH : `ssh -L 8080:127.0.0.1:8080 serveur`. Ne pas modifier la liaison Compose vers `0.0.0.0` sans ajouter une authentification multi-utilisateur et un proxy TLS adapté.

Le fichier `hdp.service` peut être copié dans `/etc/systemd/system/` après installation sous `/opt/hdp`.

## Sauvegarde

Exécuter `backup-hdp.ps1` sur Windows. Conserver ensemble l’archive et son `.sha256`. La restauration refuse les archives non authentifiées, chemins traversants, liens et bombes ZIP.
