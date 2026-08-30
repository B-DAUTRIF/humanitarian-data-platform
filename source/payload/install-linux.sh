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
    printf 'HDP_PORT=8080\nHDP_AUTH_MODE=passkey\nHDP_WEBAUTHN_RP_ID=localhost\n'
    printf 'HDP_WEBAUTHN_ORIGIN=http://localhost:8080\nHDP_COOKIE_SECURE=false\n'
    printf 'HDP_ALLOWED_HOSTS=localhost,127.0.0.1,api\n'
    printf 'RELIEFWEB_APPNAME=\nHDX_HAPI_APP_IDENTIFIER=\nGITHUB_TOKEN=\nHDP_MAX_UPLOAD_BYTES=536870912\n'
  } > .env
  echo "Configuration locale .env créée avec des secrets indépendants."
fi

port=$(sed -n 's/^HDP_PORT=//p' .env | head -n 1)
port=${port:-8080}
ensure_env() {
  key=$1
  value=$2
  if ! grep -q "^${key}=" .env; then
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}
ensure_env HDP_AUTH_MODE passkey
ensure_env HDP_WEBAUTHN_RP_ID localhost
ensure_env HDP_WEBAUTHN_ORIGIN "http://localhost:${port}"
ensure_env HDP_COOKIE_SECURE false
ensure_env HDP_ALLOWED_HOSTS localhost,127.0.0.1,api

mkdir -p data
if [ "$MODE" = "server" ]; then
  echo "Mode serveur dédié: le port reste lié à 127.0.0.1. Utilisez un tunnel SSH; ne publiez pas 8080 directement."
fi
docker compose --env-file .env -f compose.yaml up -d --build
printf 'HDP V6 est lancé: http://localhost:%s/\n' "${port:-8080}"
