# Développement et validation

## Arborescence

```text
source/payload/api/app/         API FastAPI, planificateur et sécurité
source/payload/api/static/      interface web autonome
source/payload/r-service/       module R facultatif
source/payload/runner/          runners C Python/R sans shell ni réseau
source/payload/github-api/      passerelle REST GitHub locale et verrouillée
source/src/                     installateur C/Win32 et payload généré
source/scripts/                 génération du tableau C
source/tests/                   tests Python et roundtrip C
```

## Exécution en développement

Créez `.env` à côté de `compose.yaml` :

```dotenv
POSTGRES_PASSWORD=une-valeur-aleatoire
RELIEFWEB_APPNAME=
GITHUB_TOKEN=
HDP_PORT=8080
```

Puis :

```bash
cd source/payload
docker compose up -d --build db runner-python github-api api
```

## Tests

```bash
python -m compileall -q source/payload/api/app
python -m unittest discover -s source/tests -p 'test_*.py' -v
gcc -std=c17 -O2 -Wall -Wextra -Werror source/payload/runner/runner.c -o /tmp/hdp-runner
node source/scripts/generate_payload.mjs source/payload source/src/payload_generated.h
```

Le test C de roundtrip doit être compilé après génération du payload. Il compare chaque chemin et chaque octet embarqué au contenu source. Les archives ZIP doivent passer `unzip -t` et toutes les valeurs de `SHA256SUMS.txt` doivent être recalculées après la création finale.

## Construction Windows

Depuis `source/` :

```bash
bash build.sh /chemin/vers/zig /chemin/vers/cache
```

Le résultat est `HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe`. La compilation cible `x86_64-windows-gnu`, le sous-système GUI et traite les avertissements comme erreurs.

## Validation non disponible dans un environnement sans Docker

La compilation Python, les tests unitaires et de contrat, la syntaxe JavaScript, le
roundtrip du payload, le format PE, les archives et les
empreintes peuvent être validés sans Docker. La migration PostgreSQL/PostGIS et
le parcours navigateur complet nécessitent un moteur Docker opérationnel et
doivent être exécutés sur la machine Windows de recette. L'EXE est compilable
depuis Linux avec Zig ; sa recette Windows complète demeure distincte de la
validation de compilation croisée.
