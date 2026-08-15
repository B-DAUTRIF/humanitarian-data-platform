# Livrables HDP 4.0.0

Le répertoire `dist/v4.0.0/` est généré par
`python3 tools/package_v4_release.py` depuis le gel de code indiqué dans le
manifeste.

## Archives principales

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

## Limite de l'installateur natif

Aucun exécutable d'installation 4.0.0 n'est annoncé : le compilateur Windows et
le certificat Authenticode ne sont pas disponibles dans l'environnement de
construction. L'archive portable est le livrable Windows 4.0.0. Les anciens
EXE 3.0.0 restent dans leurs archives historiques et ne sont pas renommés.
