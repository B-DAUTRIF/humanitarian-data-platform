#!/usr/bin/env sh
set -eu

MODE="${1:-workstation}"
case "$MODE" in
  workstation|server) ;;
  *) echo "Usage: $0 [workstation|server]" >&2; exit 2 ;;
esac

command -v docker >/dev/null 2>&1 || {
  echo "Docker Engine est requis: https://docs.docker.com/engine/install/" >&2
  exit 1
}
docker compose version >/dev/null 2>&1 || {
  echo "Le plugin Docker Compose v2 est requis." >&2
  exit 1
}

secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    od -An -N32 -tx1 /dev/urandom | tr -d ' \n'
  fi
}

if [ ! -f .env ]; then
  umask 077
  {
    printf 'POSTGRES_PASSWORD=%s\n' "$(secret)"
    printf 'HDP_LOCAL_TOKEN=%s\n' "$(secret)"
    printf 'HDP_SQL_PASSWORD=%s\n' "$(secret)"
    printf 'HDP_PORT=8080\nRELIEFWEB_APPNAME=\nHDX_HAPI_APP_IDENTIFIER=\nGITHUB_TOKEN=\nHDP_MAX_UPLOAD_BYTES=536870912\n'
  } > .env
  echo "Configuration locale .env créée avec des secrets indépendants."
fi

mkdir -p data
if [ "$MODE" = "server" ]; then
  echo "Mode serveur dédié: le port reste lié à 127.0.0.1. Utilisez un tunnel SSH; ne publiez pas 8080 directement."
fi
docker compose --env-file .env -f compose.yaml up -d --build
token=$(sed -n 's/^HDP_LOCAL_TOKEN=//p' .env | head -n 1)
port=$(sed -n 's/^HDP_PORT=//p' .env | head -n 1)
printf 'HDP V5 est lancé: http://127.0.0.1:%s/?token=%s\n' "${port:-8080}" "$token"
