# Construction de l'installateur 2.3.2

L'installateur est écrit en C/Win32 et compilé depuis Linux avec Zig pour Windows x64.

Prérequis : Node.js 20 ou supérieur et Zig compatible.

```bash
bash build.sh /chemin/vers/zig /chemin/vers/un-cache-temporaire
```

Le script :

1. transforme le contenu de `payload/` en tableau binaire C ;
2. compile le manifeste et les métadonnées Windows ;
3. compile le programme Win32 avec les avertissements traités comme erreurs ;
4. produit `HumanitarianDataPlatform_Setup_Native_GUI_v2.3.2.exe`.

Le test `tests/payload_roundtrip.c` valide que le tableau embarqué restitue exactement le payload. Les tests Python de `tests/test_v23_helpers.py` couvrent les chemins confinés, URL publiques, noms de fichiers, empreintes, intervalles, paramètres GitHub, hiérarchie ONU M49 et sélection stricte des COD-AB officiels.

L'installateur conserve `.env`, le volume PostgreSQL et `data/` lors d'une mise à niveau. Il sélectionne 8080 ou un port libre entre 18080 et 18279, puis garde l'API liée à `127.0.0.1`. Docker Desktop et les outils optionnels sont installés par `winget` uniquement après sélection explicite.
