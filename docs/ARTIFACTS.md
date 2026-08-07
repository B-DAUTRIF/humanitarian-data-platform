# Livrables et empreintes

Les livrables courants sont dans [`dist/v2.0`](../dist/v2.0). Les fichiers historiques originaux sont conservés dans [`dist/v1.5`](../dist/v1.5).

## Version 2.0

| Fichier | Octets | SHA-256 | Rôle |
|---|---:|---|---|
| `HumanitarianDataPlatform_Setup_Native_GUI_v2.0.exe` | 288 256 | `f02553d1e2f63c2028ca9a4353ebb7684ccaab00ff21ab56651cf55fbac5dcb9` | Installateur Windows natif x64 |
| `HumanitarianDataPlatform_Setup_Native_GUI_v2.0.exe.sha256` | 117 | `857a9eb852e079958da366ee574e8a1135d7c450c858b9059b5e76101fd9bd55` | Empreinte de l'installateur |
| `HumanitarianDataPlatform_Windows_v2.0.zip` | 114 091 | `5d7802d80bf21a0f17026be1c868f1a3487adad43c7bb668e2c4b601cf79de9b` | Paquet utilisateur Windows |
| `HumanitarianDataPlatform_Source_v2.0.zip` | 139 839 | `bbf794ecf3a869cade040e7ff792b0cac0d42666f251c1b026ef11b73b521cef` | Sources reproductibles |
| `HumanitarianDataPlatform_Archive_complete_v2.0.zip` | 388 318 | `7621177c2aee9a66c45a14dfd5b69c3f5942745546547a2908b2368f3d375f27` | Archive complète de remise |
| `HumanitarianDataPlatform_Archive_complete_v2.0.zip.sha256` | 117 | `97d68cbda6c3746b23f3647d08ad5984deec539d271348a8db79727ece33f962` | Empreinte de l'archive complète |
| `HumanitarianDataPlatform_Setup_README_v2.0.txt` | 2 848 | `301dec53836f9644de01c5aacfe21e1fe60c64f083bc25a70d73b42f469689c4` | Notice courte |
| `HDP_Diagnostic_v2.0.cmd` | 6 146 | `8aab3073e4cbcef53340af45e7f5eeef3b061ef0671978fe33fcb0b9a296116e` | Diagnostic Windows borné |
| `Notice_detaillee_Humanitarian_Data_Platform_v2.0.pdf` | 34 439 | `db883c602c158972c39ed553c003225a9a4520939b408108d916492e47f4ccf3` | Notice détaillée A4, 21 pages |
| `HDP_Prompt_exhaustif_reprise_GPT_Plus_v2.0.txt` | 8 356 | `72ccd5dec61e17b2e1beebce864a8eb08602c8bd7180ae438e9fdda1659499fb` | Prompt autonome de reprise |
| `MANIFESTE_HumanitarianDataPlatform_v2.0.txt` | 3 152 | `b53ef29abead77dfad14d1c00b0b2b1291cd24eca307ac1ce4836d0b8d39ff1f` | Constitution et validations |

`SHA256SUMS.txt` contient les empreintes de tous ces fichiers et a lui-même pour SHA-256 `ac407bfa2ef73b062126add4fcb1922f71883f3e97960dd43ca9aa37383e25fc`.

## Validation

```bash
cd dist/v2.0
sha256sum -c SHA256SUMS.txt
unzip -t HumanitarianDataPlatform_Source_v2.0.zip
unzip -t HumanitarianDataPlatform_Windows_v2.0.zip
unzip -t HumanitarianDataPlatform_Archive_complete_v2.0.zip
```
