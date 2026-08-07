# Installation et mise à niveau Windows

## Prérequis

- Windows 10 ou 11 x64 ;
- virtualisation matérielle et WSL 2 disponibles ;
- Docker Desktop opérationnel ;
- au moins 10 Gio libres recommandés ;
- accès Internet aux registres Docker et aux sources de données.

L'installateur peut proposer Docker Desktop, Git et Visual Studio Code via `winget`. Aucune case n'est cochée automatiquement. Le module R est facultatif.

## Installation

1. Décompressez `HumanitarianDataPlatform_Windows_v2.0.zip`.
2. Vérifiez l'empreinte de l'exécutable :

   ```powershell
   Get-FileHash .\HumanitarianDataPlatform_Setup_Native_GUI_v2.0.exe -Algorithm SHA256
   ```

3. Comparez le résultat au contenu de `HumanitarianDataPlatform_Setup_Native_GUI_v2.0.exe.sha256`.
4. Lancez l'exécutable et vérifiez le dossier proposé :

   ```text
   %USERPROFILE%\HumanitarianDataPlatform
   ```

5. Saisissez un appname ReliefWeb uniquement s'il a été pré-approuvé.
6. Sélectionnez explicitement les composants voulus, puis installez.

L'installateur choisit `8080` si possible, sinon un port libre entre `18080` et `18279`. La valeur est enregistrée dans `.env` et utilisée par Compose, les scripts et le navigateur.

## Mise à niveau depuis 1.5

Relancez l'installateur 2.0 en conservant le même dossier. Il remplace les fichiers applicatifs embarqués mais préserve :

- `.env`, donc le mot de passe PostgreSQL, l'appname ReliefWeb et le port ;
- le volume nommé `postgres_data` ;
- le dossier `data`, y compris les réponses brutes ;
- les images Docker déjà téléchargées.

Au premier démarrage, l'API effectue la migration idempotente. Voir [Migration depuis 1.5](MIGRATION_V2.md).

## Démarrage et arrêt

- `start-hdp.cmd` : cœur FastAPI/PostgreSQL ;
- `start-hdp-with-r.cmd` : ajoute le profil analytique R ;
- `stop-hdp.cmd` : arrête les conteneurs sans supprimer les volumes ni les fichiers.

## Répertoires

| Élément | Emplacement |
|---|---|
| Application | `%USERPROFILE%\HumanitarianDataPlatform` |
| Configuration | `%USERPROFILE%\HumanitarianDataPlatform\.env` |
| JSON bruts | `%USERPROFILE%\HumanitarianDataPlatform\data\raw` |
| Ressources | `%USERPROFILE%\HumanitarianDataPlatform\data\projects` |
| Journaux installateur | `%LOCALAPPDATA%\HumanitarianDataPlatform\logs` |

Ne supprimez pas le volume PostgreSQL ou `data/` sans sauvegarde explicite.
