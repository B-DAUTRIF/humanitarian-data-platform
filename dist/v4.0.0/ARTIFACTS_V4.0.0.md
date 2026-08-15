# Livrables HDP 4.0.0

Le répertoire `dist/v4.0.0/` est généré par
`python3 tools/package_v4_release.py` depuis le gel de code indiqué dans le
manifeste.

## Archives principales

- `HumanitarianDataPlatform_Setup_Native_GUI_v4.0.0.exe` : installateur natif
  Windows PE32+ GUI x64, compilé avec MSVC par GitHub Actions ;
- `HumanitarianDataPlatform_Windows_Portable_v4.0.0.zip` : payload autonome à
  décompresser sur Windows, puis à démarrer avec `start-hdp.cmd` et Docker
  Desktop ;
- `HumanitarianDataPlatform_Source_v4.0.0.zip` : sources, tests, outils de
  construction, documentation, workflow CI et payload embarqué ;
- `HumanitarianDataPlatform_Archive_complete_v4.0.0.zip` : archive globale
  regroupant les deux archives précédentes, la documentation de référence, le
  prompt global, la TODO, le manifeste et les sommes SHA-256.

## Vérification

Exécuter depuis le répertoire des livrables :

```powershell
Get-FileHash -Algorithm SHA256 .\HumanitarianDataPlatform_Archive_complete_v4.0.0.zip
Get-Content .\HumanitarianDataPlatform_Archive_complete_v4.0.0.zip.sha256
```

`SHA256SUMS.txt` couvre les fichiers créés avant l'archive globale. Le fichier
`.sha256` adjacent couvre l'archive globale elle-même. Le script de
conditionnement teste le CRC et les chemins de chaque ZIP.

## Installateur natif

Le workflow `HDP Windows installer` a compilé et vérifié l’EXE 4.0.0 sur un
runner Windows x64 : métadonnées 4.0.0, format PE32+ GUI x64, ASLR, NX et haute
entropie. L’exécutable et son `.sha256` sont inclus dans l’archive globale.

L’EXE n’est pas signé Authenticode et n’a pas encore subi une recette manuelle
complète sur Windows 10/11 avec Docker Desktop. Windows peut afficher un
avertissement SmartScreen. Les anciens EXE 3.0.0 restent inchangés dans leurs
archives historiques.
