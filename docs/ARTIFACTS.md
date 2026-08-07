# Livrables et empreintes

Les livrables courants sont dans [`dist/v2.4.0`](../dist/v2.4.0). Les versions historiques restent intactes dans [`dist/v2.3.2`](../dist/v2.3.2), [`dist/v2.3.1`](../dist/v2.3.1), [`dist/v2.0`](../dist/v2.0) et [`dist/v1.5`](../dist/v1.5).

## Version 2.4.0

| Fichier | Rôle |
|---|---|
| `HumanitarianDataPlatform_Setup_Native_GUI_v2.4.0.exe` | Installateur Windows natif x64 |
| `HumanitarianDataPlatform_Setup_Native_GUI_v2.4.0.exe.sha256` | Empreinte de l'installateur |
| `HumanitarianDataPlatform_Windows_v2.4.0.zip` | Paquet utilisateur Windows |
| `HumanitarianDataPlatform_Source_v2.4.0.zip` | Sources reproductibles |
| `HumanitarianDataPlatform_Archive_complete_v2.4.0.zip` | Archive complète de remise |
| `HumanitarianDataPlatform_Archive_complete_v2.4.0.zip.sha256` | Empreinte de l'archive complète |
| `HumanitarianDataPlatform_Setup_README_v2.4.0.txt` | Notice courte |
| `CHANGELOG_HDP_v2.4.0.log` | Journal applicatif de la sous-version |
| `HDP_Configurer_GitHub_v2.4.0.cmd` | Configuration sûre du jeton GitHub sous Windows |
| `HDP_Diagnostic_v2.4.0.cmd` | Diagnostic Windows borné et sans secret `.env` |
| `Notice_detaillee_Humanitarian_Data_Platform_v2.4.0.pdf` | Notice détaillée A4 vérifiée visuellement |
| `HDP_Prompt_exhaustif_reprise_GPT_Plus_v2.4.0.txt` | Prompt autonome de reprise |
| `MANIFESTE_HumanitarianDataPlatform_v2.4.0.txt` | Constitution et validations |

Les tailles et empreintes exactes de la remise sont dans [`SHA256SUMS.txt`](../dist/v2.4.0/SHA256SUMS.txt). Le manifeste reprend aussi les contrôles exécutés et les limites de la recette.

## Validation

```bash
cd dist/v2.4.0
sha256sum -c SHA256SUMS.txt
unzip -t HumanitarianDataPlatform_Source_v2.4.0.zip
unzip -t HumanitarianDataPlatform_Windows_v2.4.0.zip
unzip -t HumanitarianDataPlatform_Archive_complete_v2.4.0.zip
```

L'archive complète et son propre fichier `.sha256` ne figurent pas dans `SHA256SUMS.txt`, car ce fichier est intégré à l'archive complète. Leur empreinte dédiée est fournie séparément.
