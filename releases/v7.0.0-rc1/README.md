# HDP V7.0.0 — candidat qualifié

Ce répertoire trace la livraison candidate V7. Les binaires ne sont pas stockés dans le Git source : ils sont construits sur runner Windows par le workflow **HDP V7 full qualification** et conservés comme artefact GitHub Actions `HDP-V7-qualified-candidate`.

Le paquet attendu contient :

- `HumanitarianDataPlatform_Setup_Native_GUI_v7.0.0.exe`
- `HumanitarianDataPlatform_Setup_Native_GUI_v7.0.0.exe.sha256`
- `HumanitarianDataPlatform_Archive_complete_v7.0.0.zip`
- `HumanitarianDataPlatform_Archive_complete_v7.0.0.zip.sha256`
- `HDP_V7_ARTIFACT_MANIFEST.json`

L'archive complète contient les sources, les clients R/Python, la documentation, les outils de qualification et un manifeste de provenance de build. Le manifeste final GitHub Actions relie les deux livrables à l'identifiant de commit et à l'identifiant du workflow qui les a produits.

Aucune promotion vers `main` ne doit être effectuée tant que les contrôles sémantiques, les cas d'usage, le sentinel fournisseur, les tests de non-régression V6 et la construction Windows ne sont pas tous concluants.
