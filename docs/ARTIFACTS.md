# Inventaire des livrables v1.5

Les livrables originaux sont conservés dans [`dist/`](../dist/). Les sources sont aussi extraites dans [`source/`](../source/) pour être consultables directement sur GitHub.

La liste directement vérifiable est disponible dans [`dist/SHA256SUMS.txt`](../dist/SHA256SUMS.txt).

| Fichier | Taille | SHA-256 | Rôle |
|---|---:|---|---|
| `HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe` | 219 136 octets | `1e77042dbbd7a7d400c690076bc61e3c7191c5e928cdb016a39292af2a362470` | Installateur Windows natif x64 |
| `HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe.sha256` | 117 octets | `bb8399a699faa7a5a81e5cdf91e9241bccd8fb0e291312a4606fc8160cb3b5d9` | Empreinte attendue de l'exécutable |
| `HumanitarianDataPlatform_Windows_v1.5.zip` | 100 245 octets | `51198e245dbda1c11b3c24cd700b8fe15c2cab3f9b7ea3bcf0f6acb9f6343976` | Paquet utilisateur Windows |
| `HumanitarianDataPlatform_Source_v1.5.zip` | 49 676 octets | `6f63234435a97760da847d1c0ce87573def7e216fb7ee24f9a34229e6328f6e2` | Sources reproductibles originales |
| `HumanitarianDataPlatform_Setup_README_v1.5.txt` | 3 045 octets | `f7e0db51546cdab6109acab2c472e2238781e2b3599d3a102dd6ae9f6c4288c5` | Notice courte |
| `HDP_Diagnostic_v1.5.cmd` | 5 904 octets | `85f80513f3080e3b88244edf5b9fe465af10c08c07a72f0e8dc4cffc7282e3ec` | Diagnostic Windows |
| `Notice_detaillee_Humanitarian_Data_Platform_v1.5.pdf` | 149 908 octets | `f0ba5920904aeb84a14d6e25d1f2f371a3abe3c4e6c81bba2de39f7fef396a41` | Notice détaillée de 23 pages A4 |
| `HDP_Prompt_exhaustif_reprise_GPT_Plus_v1.5.txt` | 19 809 octets | `5b0717d213ded9574f18c4ac6242f5519d10331ab7485cc82fa1cd6f12981450` | Prompt autonome de reprise |
| `generate_notice_v15.py` | 46 940 octets | `3b2eab800b346a2efcc6c29418a66f36afaeb2ec1c511b814009a0d407ef225d` | Source de la notice PDF |
| `HumanitarianDataPlatform_Archive_complete_v1.5.zip` | 378 621 octets | `caf657d89e072a443e90762240d06467c668bbe2ada45afdd0adc04a0365314f` | Archive complète originale |

Le fichier `MANIFESTE_HumanitarianDataPlatform_v1.5.txt` décrit la constitution de l'archive. Son empreinte n'était volontairement pas inscrite dans le manifeste lui-même.

## Contenu du paquet Windows

```text
HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe
HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe.sha256
HumanitarianDataPlatform_Setup_README_v1.5.txt
HDP_Diagnostic_v1.5.cmd
```

## Contenu source principal

```text
SOURCE_BUILD.md
build.sh
src/
scripts/
tests/
payload/
HumanitarianDataPlatform_Setup_README_v1.5.txt
HDP_Diagnostic_v1.5.cmd
```

## Exclusions volontaires

- le journal `HDP_Debug_v1.5_20260807_134201.log`, car il contient des informations propres à la machine Windows ;
- les versions 1.1 à 1.4, afin d'éviter l'installation accidentelle d'un paquet obsolète ;
- les fichiers `.env`, données acquises et secrets locaux.

## Vérification

Depuis `dist/` :

```bash
sha256sum -c HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe.sha256
sha256sum -c HumanitarianDataPlatform_Archive_complete_v1.5.zip.sha256
unzip -t HumanitarianDataPlatform_Source_v1.5.zip
unzip -t HumanitarianDataPlatform_Windows_v1.5.zip
unzip -t HumanitarianDataPlatform_Archive_complete_v1.5.zip
```
