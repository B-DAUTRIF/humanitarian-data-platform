# Passerelle REST GitHub - HDP 3.0.0

HDP embarque le service Docker `github-api`, une passerelle locale et bornée
vers les fonctions REST GitHub utilisées par le projet. Elle complète la
création de dépôt disponible dans l'API principale.

## Sécurité

- le service est publié uniquement sur `127.0.0.1` ;
- `GITHUB_TOKEN` reste côté serveur et n'est jamais renvoyé ;
- les lectures sont disponibles par défaut ;
- les écritures sont désactivées par défaut ;
- le conteneur est non privilégié, en lecture seule, avec limites de mémoire,
  CPU et processus ;
- propriétaire, dépôt, workflow, pagination et tailles de corps sont validés ;
- l'API REST est appelée avec `X-GitHub-Api-Version: 2026-03-10` par défaut.

HDP demeure une application locale sans authentification. Ne publiez jamais le
port 8091 sur le réseau local ou Internet.

## Configuration

Variables optionnelles dans `.env` :

```dotenv
GITHUB_TOKEN=
GITHUB_API_VERSION=2026-03-10
GITHUB_DEFAULT_OWNER=B-DAUTRIF
GITHUB_DEFAULT_REPOSITORY=humanitarian-data-platform
GITHUB_API_WRITE_ENABLED=false
GITHUB_API_TIMEOUT_SECONDS=20
HDP_GITHUB_API_PORT=8091
```

Ne versionnez jamais un jeton réel. Préférez un jeton finement granulé limité
au propriétaire et aux dépôts nécessaires.

## Endpoints locaux

| Méthode | Route | Fonction |
|---|---|---|
| GET | `/health` | Version, état du jeton et verrou d'écriture |
| GET | `/repository` | Métadonnées du dépôt |
| GET | `/branches` | Branches paginées |
| GET | `/commits` | Commits paginés, filtre `sha` facultatif |
| GET | `/issues` | Issues paginées |
| GET | `/pulls` | Pull requests paginées |
| GET | `/releases` | Releases paginées |
| GET | `/workflows` | Workflows GitHub Actions |
| GET | `/contents/{path}` | Contenu ou métadonnées d'un chemin |
| GET | `/rate-limit` | Quotas du jeton ou de l'adresse appelante |
| POST | `/issues` | Création d'une issue, verrouillée par défaut |
| POST | `/workflows/{id}/dispatch` | Déclenchement manuel, verrouillé par défaut |

Les listes acceptent `page` et `per_page` entre 1 et 100. Les métadonnées de
pagination et de quota sont retournées sans recopier d'en-tête sensible.

## Activation des écritures

Les écritures nécessitent simultanément :

1. `GITHUB_API_WRITE_ENABLED=true` ;
2. un `GITHUB_TOKEN` configuré ;
3. les permissions GitHub minimales adaptées à l'opération.

Pour un jeton finement granulé :

- création d'issue : permission **Issues: write** sur le dépôt visé ;
- déclenchement de workflow : permission **Actions: write** ;
- création d'un dépôt depuis l'API principale : permission
  **Administration: write**.

N'accordez pas **Contents: write** tant qu'aucune publication de fichiers par
l'application n'est prévue.

## Exemples locaux

```bash
curl http://127.0.0.1:8091/health
curl http://127.0.0.1:8091/repository
curl "http://127.0.0.1:8091/branches?per_page=20&page=1"
curl "http://127.0.0.1:8091/commits?sha=main"
curl "http://127.0.0.1:8091/issues?state=open"
curl http://127.0.0.1:8091/workflows
```

Références : [API REST GitHub](https://docs.github.com/en/rest),
[versionnement](https://docs.github.com/en/rest/about-the-rest-api/api-versions)
et [jetons personnels](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).
