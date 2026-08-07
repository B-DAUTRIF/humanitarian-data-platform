# Construction et validation

## Arborescence source

| Chemin | Contenu |
|---|---|
| `source/src/installer.c` | Installateur C/Win32 |
| `source/src/installer.manifest` | Manifeste Windows |
| `source/src/installer.rc` | Ressources et métadonnées Windows |
| `source/src/payload_generated.h` | Payload converti en tableaux binaires C |
| `source/payload/` | Application Docker Compose embarquée |
| `source/scripts/generate_payload.mjs` | Générateur déterministe du payload C |
| `source/tests/payload_roundtrip.c` | Reconstruction de contrôle du payload |
| `source/build.sh` | Construction croisée Windows x64 |
| `tools/generate_notice_v15.py` | Générateur de la notice PDF |

## Prérequis de construction

- environnement Linux ou compatible Bash ;
- Node.js 20 ou supérieur ;
- Zig compatible avec la chaîne testée (référence : 0.12.0-dev.1286) ;
- outils standard `sha256sum`, `unzip` et un compilateur C pour le test de reconstruction.

## Construire l'installateur

Depuis `source/` :

```bash
bash build.sh /chemin/vers/zig /chemin/vers/un-cache-temporaire
```

Le script :

1. transforme `payload/` en `src/payload_generated.h` ;
2. compile les ressources et le manifeste Windows ;
3. compile l'installateur C avec `-Wall -Wextra -Werror` ;
4. cible `x86_64-windows-gnu` et le sous-système graphique ;
5. produit `HumanitarianDataPlatform_Setup_Native_GUI_v1.5.exe`.

L'installateur dépend seulement des DLL système Windows. Les composants tiers sélectionnés sont installés sur la machine cible via winget après confirmation.

## Vérifier le payload embarqué

Régénération déterministe :

```bash
node scripts/generate_payload.mjs payload /tmp/payload_generated.h
cmp /tmp/payload_generated.h src/payload_generated.h
```

Reconstruction des fichiers :

```bash
cc -std=c11 -Wall -Wextra -Werror tests/payload_roundtrip.c -o /tmp/payload_roundtrip
mkdir -p /tmp/hdp-payload
/tmp/payload_roundtrip /tmp/hdp-payload
diff -r payload /tmp/hdp-payload
```

Le test attendu reconstruit exactement les douze fichiers du payload.

## Vérifications Python, YAML et archives

```bash
python -m py_compile payload/api/app/main.py
python - <<'PY'
from pathlib import Path
import yaml

yaml.safe_load(Path("payload/compose.yaml").read_text(encoding="utf-8"))
PY
unzip -t ../dist/HumanitarianDataPlatform_Source_v1.5.zip
unzip -t ../dist/HumanitarianDataPlatform_Windows_v1.5.zip
```

## Validation Windows de référence

Le 7 août 2026, la v1.5 a été validée sur Windows 11 Professionnel x64 avec WSL 2 et Docker Desktop :

- sélection automatique du port `18080` lorsque `8080` était indisponible ;
- conteneurs `api` et `db` sains ;
- réponses HTTP 200 sur `/` et `/api/health` ;
- PostgreSQL/PostGIS initialisé et persistant.

Cette validation démontre l'installation sur la machine testée ; elle ne remplace pas des tests automatisés sur plusieurs versions de Windows.

## Versionnement

Toute évolution doit :

- conserver le JSON source ;
- documenter les transformations ;
- tester la provenance et l'intégrité ;
- préserver l'isolation de PostgreSQL et R ;
- mettre à jour la version, les empreintes, les archives et la documentation ensemble.
