# Livrables HDP 4.1.0

Le répertoire `dist/v4.1.0/` contient :

- `HumanitarianDataPlatform_Archive_complete_v4.1.0.zip` : tous les livrables ;
- `HumanitarianDataPlatform_Source_v4.1.0.zip` : code, tests, outils et docs ;
- `HumanitarianDataPlatform_Windows_Portable_v4.1.0.zip` : payload Compose ;
- `HumanitarianDataPlatform_Setup_Native_GUI_v4.1.0.exe` : installeur x64 ;
- `Notice_detaillee_Humanitarian_Data_Platform_v4.1.0.pdf` ;
- `SHA256SUMS.txt`, manifeste et fichiers `.sha256` adjacents.

Vérification PowerShell :

```powershell
Get-FileHash .\HumanitarianDataPlatform_Archive_complete_v4.1.0.zip -Algorithm SHA256
Get-Content .\HumanitarianDataPlatform_Archive_complete_v4.1.0.zip.sha256
```

Les ZIP sont produits avec des horodatages déterministes, relus par CRC et
contrôlés contre les chemins absolus ou traversants. L'archive source exclut
les secrets, données locales, caches Python et binaires de compilation.
