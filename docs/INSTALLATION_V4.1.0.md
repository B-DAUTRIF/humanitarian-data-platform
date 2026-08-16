# Installation Windows - HDP 4.1.0

## Prérequis

- Windows 10/11 x64 ;
- Docker Desktop avec Docker Compose ;
- droits d'écriture sur le dossier d'installation ;
- R uniquement si le service et les scripts R sont nécessaires.

## Installateur natif

1. Télécharger `HumanitarianDataPlatform_Setup_Native_GUI_v4.1.0.exe` et son
   fichier `.sha256`.
2. Contrôler l'empreinte :

```powershell
Get-FileHash .\HumanitarianDataPlatform_Setup_Native_GUI_v4.1.0.exe -Algorithm SHA256
Get-Content .\HumanitarianDataPlatform_Setup_Native_GUI_v4.1.0.exe.sha256
```

3. Lancer l'EXE et choisir **Installer / mettre à niveau**.
4. Ouvrir l'URL locale indiquée par l'installateur.

L'EXE est un PE32+ GUI x64 avec ASLR, NX et haute entropie. Il n'est pas signé
Authenticode ; une politique d'entreprise peut donc imposer l'archive portable.

## Archive portable

Vérifier l'empreinte de
`HumanitarianDataPlatform_Windows_Portable_v4.1.0.zip`, décompresser dans un
nouveau dossier, puis lancer `start-hdp.cmd`.

## Mise à niveau depuis 4.0.0

1. Exécuter `backup-hdp.ps1`.
2. Conserver l'ancien dossier jusqu'à validation du redémarrage.
3. Installer 4.1.0 dans le dossier choisi. L'installateur conserve `.env`,
   `data/` et le volume PostgreSQL et crée `.env.backup-before-v4.1.0` avant
   réécriture.
4. Vérifier les paramètres de chaque source : les valeurs 4.0.0 sont fusionnées
   avec les nouveaux réglages par défaut.
5. Tester une prévisualisation puis une recherche représentative.

Une recette Windows 10/11 réelle et la signature Authenticode restent des
contrôles externes au gel automatisé.
