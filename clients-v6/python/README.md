# HDP Clients Python 6.0.0

Client Python typé pour l'API locale de Humanitarian Data Platform V6.

Le client passe volontairement par le serveur HDP au lieu d'appeler les fournisseurs en contournant l'application. Les validations propres aux sources, préférences de projet, limites de téléchargement, provenance, authentification et contrôles de sécurité restent donc appliqués.

## Installation de développement

```bash
python -m pip install -e clients-v6/python
```

## Exemple

```python
from hdp_clients import HDPClient

hdp = HDPClient("http://localhost:8080")
print(hdp.inventory_sources())

rows = hdp.inventory(source="hdx", query="package_search", supported=True)
for row in rows["rows"]:
    print(row["Paramètre"], row["Contrôle recommandé"])
```

Pour une instance configurée en authentification par jeton, passer `token=...`. En mode passkey, le navigateur reste le client recommandé pour l'établissement de la session ; le paquet Python n'essaie pas d'extraire ou de reproduire une credential WebAuthn.

## API exposée

- `health()`
- `sources()`
- `inventory_sources()`
- `inventory(...)`
- `source_inventory(source_slug)`
- `projects()` / `create_project(...)`
- `project_sources(project_id)`
- `source_settings(source_id)`
- `search(...)`
- `federated_search(...)`

`federated_search()` conserve séparément les succès et erreurs de chaque source afin de ne pas masquer une réponse partielle.
