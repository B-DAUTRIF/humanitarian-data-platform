# Livrables et empreintes — version finale 3.0.0

La remise finale est publiée sous `dist/v3.0.0/`. Le fichier à télécharger en
priorité est `HumanitarianDataPlatform_Archive_complete_v3.0.0.zip`.

| Fichier | Rôle |
|---|---|
| `HumanitarianDataPlatform_Archive_complete_v3.0.0.zip` | archive globale de tous les livrables finaux |
| `HumanitarianDataPlatform_Archive_complete_v3.0.0.zip.sha256` | empreinte dédiée de l'archive globale |
| `HumanitarianDataPlatform_Windows_v3.0.0.zip` | paquet utilisateur Windows |
| `HumanitarianDataPlatform_Source_v3.0.0.zip` | sources reproductibles et tests |
| `HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe` | installateur Windows natif PE32+ GUI x64 |
| `HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe.sha256` | empreinte de l'installateur |
| `Documentation_Humanitarian_Data_Platform_v3.0.0.html` | documentation consolidée consultable |
| `Notice_detaillee_Humanitarian_Data_Platform_v3.0.0.pdf` | documentation consolidée imprimable |
| `HDP_Prompt_production_global_v3.0.0.txt` | prompt autonome de production et reconstruction |
| `MANIFESTE_HumanitarianDataPlatform_v3.0.0.txt` | constitution, versions, contrôles et limites |
| `SHA256SUMS.txt` | sommes des livrables intégrés à l'archive globale |

L'archive globale contient en outre la documentation Markdown, le cahier des
charges, la référence API, les rapports de validation, la matrice de
compatibilité, le registre de décisions et les journaux `LOG-Huma`.

## Validation

```bash
cd dist/v3.0.0
sha256sum -c SHA256SUMS.txt
sha256sum -c HumanitarianDataPlatform_Archive_complete_v3.0.0.zip.sha256
unzip -t HumanitarianDataPlatform_Source_v3.0.0.zip
unzip -t HumanitarianDataPlatform_Windows_v3.0.0.zip
unzip -t HumanitarianDataPlatform_Archive_complete_v3.0.0.zip
```

L'archive globale ne peut pas contenir sa propre empreinte. Son fichier
`.sha256` est donc fourni à côté et vérifié séparément.

## Historique

Les répertoires `dist/v2.5.0`, `dist/v2.4.0`, `dist/v2.3.2`, `dist/v2.3.1`,
`dist/v2.0` et `dist/v1.5` restent des références historiques et ne remplacent
pas la remise finale 3.0.0.
