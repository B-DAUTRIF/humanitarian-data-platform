#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "6.0.0"


def require(text: str, marker: str, label: str) -> None:
    if marker not in text:
        raise SystemExit(f"Contrôle sécurité absent ({label}): {marker}")


def forbid(text: str, marker: str, label: str) -> None:
    if marker in text:
        raise SystemExit(f"Contrôle sécurité échoué ({label}): {marker}")


def main() -> None:
    compose = (ROOT / "source/payload/compose.yaml").read_text(encoding="utf-8")
    main_source = (ROOT / "source/payload/api/app/main.py").read_text(encoding="utf-8")
    sql = (ROOT / "source/payload/api/app/sql_workspace.py").read_text(encoding="utf-8")
    installer = (ROOT / "source/src/installer.c").read_text(encoding="utf-8")
    require(compose, '127.0.0.1:${HDP_PORT:-8080}:8080', "API liée à localhost")
    require(compose, "network_mode: none", "runners hors réseau")
    require(compose, 'cap_drop: ["ALL"]', "capacités supprimées")
    forbid(compose, "5432:5432", "PostgreSQL non publié")
    require(main_source, "SET TRANSACTION READ ONLY", "transaction SQL read-only")
    require(sql, "ALLOWED_SQL_FUNCTIONS", "liste positive des fonctions SQL")
    require(sql, "parse_sql_json", "analyse SQL par AST PostgreSQL")
    require(main_source, "sql_reader_connection", "rôle SQL dédié")
    require(main_source, "local_request_boundary", "frontière HTTP locale")
    require(main_source, "validate_public_url", "contrôle SSRF")
    require(main_source, "validate_upload_content", "validation d’import")
    require(main_source, "download_public_file", "transport HTTP à IP épinglée")
    require(installer, f".env.backup-before-v{VERSION}", "sauvegarde de configuration V6")
    forbid(installer, ".env.backup-before-v5.0.2", "aucun contrat de sauvegarde V5 actif")
    forbid(installer.casefold(), "down -v", "aucune suppression de volume")
    print(f"Contrôles de sécurité statiques HDP {VERSION}: OK")


if __name__ == "__main__":
    main()
