# Construction de l'installateur 6.0.0-dev

L'installateur est écrit en C/Win32 et compilé depuis Linux avec Zig pour Windows x64.

Prérequis : Node.js 20 ou supérieur et Zig compatible.

```bash
bash build.sh /chemin/vers/zig /chemin/vers/un-cache-temporaire
```

Le script :

1. transforme le contenu de `payload/` en tableau binaire C ;
2. compile le manifeste et les métadonnées Windows ;
3. compile le programme Win32 avec les avertissements traités comme erreurs ;
4. produit `HumanitarianDataPlatform_Setup_Native_GUI_v6.0.0-dev.exe`.

Le test `tests/payload_roundtrip.c` valide que le tableau embarqué restitue exactement le payload. La suite Python couvre aussi le registre versionné des sources, les migrations idempotentes, les contrats d'interface, les chemins confinés, URL publiques, noms de fichiers, empreintes, intervalles, paramètres GitHub, ONU M49, familles COD officielles, le catalogue sanitaire, RSS, GeoJSON et les contrats des runners.

L'installateur conserve toutes les variables inconnues de `.env`, les secrets déjà présents, le volume PostgreSQL et `data/` lors d'une mise à niveau. Les migrations sont transactionnelles et enregistrées dans `schema_migrations`. Il sélectionne 8080 ou un port libre entre 18080 et 18279, puis garde l'API liée à `127.0.0.1`. Docker Desktop et les outils optionnels sont installés par `winget` uniquement après sélection explicite.

La compilation contrôlée sur Windows x64 produit un artefact de développement.
La qualification finale reste distincte : installation neuve, mise à niveau
depuis 5.0.2, conservation de `.env`, des fichiers et du volume PostgreSQL,
démarrage, contrôle de santé et vérification du raccourci Bureau.
