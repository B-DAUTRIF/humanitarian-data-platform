# Installation et mise à niveau Windows

## Prérequis

- Windows 10 ou 11 x64 ;
- virtualisation matérielle et WSL 2 disponibles ;
- Docker Desktop opérationnel ;
- au moins 10 Gio libres recommandés ;
- accès Internet aux registres Docker et aux sources de données.

L'installateur peut proposer Docker Desktop, Git et Visual Studio Code via `winget`. Aucune case n'est cochée automatiquement. Le module R est facultatif.

## Installation

1. Décompressez `HumanitarianDataPlatform_Windows_v3.0.0.zip`.
2. Vérifiez l'empreinte de l'exécutable :

   ```powershell
   Get-FileHash .\HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe -Algorithm SHA256
   ```

3. Comparez le résultat au contenu de `HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe.sha256`.
4. Lancez l'exécutable et vérifiez le dossier proposé :

   ```text
   %USERPROFILE%\HumanitarianDataPlatform
   ```

5. Saisissez un appname ReliefWeb uniquement s'il a été pré-approuvé.
6. Facultatif : saisissez un jeton GitHub autorisé à créer les dépôts souhaités. Le champ est masqué.
7. Sélectionnez explicitement les composants voulus, puis installez.

L'installateur choisit `8080` si possible, sinon un port libre entre `18080` et `18279`. La valeur est enregistrée dans `.env` et utilisée par Compose, les scripts et le navigateur.

## Mise à niveau depuis 2.5.0

Relancez l'installateur 3.0.0 en conservant le même dossier. Il remplace les fichiers applicatifs embarqués mais préserve :

- `.env`, donc le mot de passe PostgreSQL, l'appname ReliefWeb, le jeton GitHub,
  le port et toute autre variable inconnue de l'installateur ;
- le volume nommé `postgres_data` ;
- le dossier `data`, y compris les réponses brutes ;
- les images Docker déjà téléchargées.

Au premier démarrage, l'API effectue la migration idempotente et enregistre sa
version. Voir [Migration vers 3.0.0](MIGRATION_V2.md). La compatibilité de la
structure 2.5.0 est couverte par les contrats de l'itération 1. La qualification
des versions 1.5 à 2.4 nécessite les archives ou sauvegardes correspondantes.

Après une mise à niveau depuis 2.3.x, vérifiez le profil géographique de chaque
projet. Un profil déjà limité à un pays ou une zone est conservé avec COD-AB
sélectionné. Une portée monde ou région est suspendue : choisissez explicitement
un pays ou une zone dans la nouvelle liste ONU M49 × HDX, puis enregistrez.

L'activation de COD-PS peut réduire la liste : au 7 août 2026, Algérie est
disponible pour COD-AB mais pas pour COD-PS, tandis que Soudan est disponible
pour les deux. HDP ne remplace jamais automatiquement un territoire devenu
incompatible.

## Démarrage et arrêt

- `start-hdp.cmd` : cœur FastAPI/PostgreSQL et runner Python sans réseau ;
- `start-hdp-with-r.cmd` : ajoute R/plumber et le runner R sans réseau ;
- `stop-hdp.cmd` : arrête les conteneurs sans supprimer les volumes ni les fichiers.

La passerelle GitHub locale est démarrée avec le cœur sur `127.0.0.1:8091` par
défaut. Elle reste en lecture seule fonctionnelle tant que
`GITHUB_API_WRITE_ENABLED=false`.

## Répertoires

| Élément | Emplacement |
|---|---|
| Application | `%USERPROFILE%\HumanitarianDataPlatform` |
| Configuration | `%USERPROFILE%\HumanitarianDataPlatform\.env` |
| JSON bruts | `%USERPROFILE%\HumanitarianDataPlatform\data\raw` |
| Ressources | `%USERPROFILE%\HumanitarianDataPlatform\data\projects` |
| Rapports d'exécution | `%USERPROFILE%\HumanitarianDataPlatform\data\projects\<projet>\executions` |
| Journaux installateur | `%LOCALAPPDATA%\HumanitarianDataPlatform\logs` |

Ne supprimez pas le volume PostgreSQL ou `data/` sans sauvegarde explicite.
