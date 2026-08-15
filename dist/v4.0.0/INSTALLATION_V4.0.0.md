# Installation Windows - HDP 4.0.0

## Prérequis

- Windows 10/11 x64 ;
- Docker Desktop avec Compose v2 ;
- PowerShell pour les contrôles, sauvegardes et restaurations ;
- au moins 4 Gio de mémoire disponible et un espace disque adapté aux données.

## Installation native

1. Téléchargez `HumanitarianDataPlatform_Setup_Native_GUI_v4.0.0.exe` et son
   fichier `.sha256`.
2. Contrôlez l’empreinte :

   ```powershell
   Get-FileHash .\HumanitarianDataPlatform_Setup_Native_GUI_v4.0.0.exe -Algorithm SHA256
   Get-Content .\HumanitarianDataPlatform_Setup_Native_GUI_v4.0.0.exe.sha256
   ```

3. Double-cliquez sur l’EXE, choisissez le dossier et les composants, puis
   lancez **Installer / mettre à niveau**. Une installation existante conserve
   `.env`, `data/` et le volume PostgreSQL ; une sauvegarde de `.env` est créée.
4. Laissez Docker Desktop terminer son initialisation et acceptez vous-même ses
   conditions si son interface le demande.

L’EXE n’est pas signé Authenticode. Windows peut afficher un avertissement
SmartScreen ; vérifiez impérativement le SHA-256 avant de l’autoriser.

## Installation portable de repli

1. Téléchargez `HumanitarianDataPlatform_Windows_Portable_v4.0.0.zip` et son
   empreinte depuis l’archive globale.
2. Contrôlez le fichier :

   ```powershell
   Get-FileHash .\HumanitarianDataPlatform_Windows_Portable_v4.0.0.zip -Algorithm SHA256
   ```

3. Décompressez-le dans un dossier utilisateur non synchronisé publiquement.
4. Copiez `.env.example` vers `.env` et remplacez `POSTGRES_PASSWORD` par une
   valeur aléatoire longue. Renseignez facultativement `RELIEFWEB_APPNAME`,
   `HDX_HAPI_APP_IDENTIFIER` et `GITHUB_TOKEN`.
5. Lancez `start-hdp.cmd`. L’application ouvre `http://localhost:8080` ou le
   port indiqué par `HDP_PORT`.
6. Activez R avec `start-hdp-with-r.cmd` uniquement si nécessaire.

PostgreSQL n’est pas publié et les services HTTP sont liés à `127.0.0.1`.

## Mise à niveau depuis 3.0.0

Sauvegardez d’abord avec `backup-hdp.ps1`. Conservez l’ancien dossier, copiez
le nouveau payload dans un dossier distinct, reportez `.env` et `data/`, puis
démarrez 4.0.0. Les migrations sont idempotentes et ne suppriment pas les
tables historiques. Ne lancez jamais `docker compose down -v`.

Le workflow GitHub Actions `HDP Windows installer` reconstruit le payload puis
compile `HumanitarianDataPlatform_Setup_Native_GUI_v4.0.0.exe` avec MSVC sur un
runner Windows x64. Il vérifie les métadonnées 4.0.0 et le format PE32+ GUI x64,
puis publie l’EXE et son empreinte SHA-256 comme artefact. N’utilisez pas l’EXE
3.0.0 comme preuve d’installation de 4.0.0.

La compilation et les contrôles statiques de l’installateur ont réussi. Une
recette manuelle complète sur Windows 10/11 avec Docker Desktop reste à mener.

## Diagnostic

- `docker compose ps` : état des services ;
- `docker compose logs --tail 200 api` : journaux API à relire avant partage ;
- `/api/health` : version, base, planificateur et runners ;
- `python tools/security_static_checks.py` : invariants de configuration dans
  une copie des sources.
