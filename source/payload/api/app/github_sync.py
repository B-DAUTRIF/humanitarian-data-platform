from __future__ import annotations

"""Synchronisation GitHub par utilisateur et par projet pour HDP.

Principes de sécurité:
- aucun jeton GitHub n'est stocké dans PostgreSQL;
- un profil utilisateur référence uniquement le nom d'une variable d'environnement;
- chaque projet choisit explicitement dépôt, branche, sens et chemins autorisés;
- aucune suppression distante automatique;
- toute divergence simultanée produit un conflit explicite plutôt qu'un écrasement.
"""

import base64
import hashlib
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import psycopg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

DATABASE_URL = os.environ["DATABASE_URL"]
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
GITHUB_API = "https://api.github.com"
SYNC_DIRECTIONS = {"push", "pull", "bidirectional"}
CONFLICT_POLICIES = {"stop", "prefer_local", "prefer_remote"}
TOKEN_ENV_RE = re.compile(r"^HDP_GITHUB_TOKEN_[A-Z0-9_]{1,80}$")
SAFE_REPO_PATH = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/@+ -]{1,500}$")

router = APIRouter(prefix="/api/github-sync", tags=["GitHub sync"])


def db() -> psycopg.Connection[Any]:
    return psycopg.connect(DATABASE_URL, autocommit=True)


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_schema() -> None:
    """Crée de façon idempotente les tables de configuration et d'audit."""
    with db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS github_user_profiles (
                id UUID PRIMARY KEY,
                display_name TEXT NOT NULL,
                github_login TEXT NOT NULL,
                token_env_name TEXT NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                UNIQUE (github_login, token_env_name)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS project_github_sync (
                project_id UUID PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
                user_profile_id UUID NOT NULL REFERENCES github_user_profiles(id),
                repository_owner TEXT NOT NULL,
                repository_name TEXT NOT NULL,
                branch TEXT NOT NULL DEFAULT 'main',
                direction TEXT NOT NULL DEFAULT 'bidirectional',
                conflict_policy TEXT NOT NULL DEFAULT 'stop',
                enabled BOOLEAN NOT NULL DEFAULT FALSE,
                interval_minutes INTEGER NOT NULL DEFAULT 60,
                include_paths JSONB NOT NULL DEFAULT '["scripts", "docs", "exports"]'::jsonb,
                remote_prefix TEXT NOT NULL DEFAULT 'hdp',
                last_local_fingerprint TEXT,
                last_remote_commit TEXT,
                last_sync_at TIMESTAMPTZ,
                next_sync_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                CHECK (direction IN ('push','pull','bidirectional')),
                CHECK (conflict_policy IN ('stop','prefer_local','prefer_remote')),
                CHECK (interval_minutes BETWEEN 15 AND 43200)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS github_sync_runs (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                user_profile_id UUID NOT NULL REFERENCES github_user_profiles(id),
                started_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ,
                status TEXT NOT NULL,
                direction TEXT NOT NULL,
                remote_commit_before TEXT,
                remote_commit_after TEXT,
                local_fingerprint_before TEXT,
                local_fingerprint_after TEXT,
                changed_files JSONB NOT NULL DEFAULT '[]'::jsonb,
                conflicts JSONB NOT NULL DEFAULT '[]'::jsonb,
                message TEXT NOT NULL DEFAULT ''
            )
            """
        )


def validate_token_env_name(value: str) -> str:
    name = value.strip().upper()
    if not TOKEN_ENV_RE.fullmatch(name):
        raise ValueError("Nom de secret attendu: HDP_GITHUB_TOKEN_<UTILISATEUR>")
    return name


def token_for_profile(profile: dict[str, Any]) -> str:
    token = os.getenv(str(profile["token_env_name"]), "").strip()
    if not token:
        raise HTTPException(409, "Jeton GitHub absent de la configuration serveur pour cet utilisateur")
    return token


def safe_repo_path(value: str) -> str:
    path = value.replace("\\", "/").strip("/")
    if not SAFE_REPO_PATH.fullmatch(path):
        raise ValueError(f"Chemin GitHub refusé: {value}")
    return path


def project_root(project_id: uuid.UUID) -> Path:
    root = (DATA_DIR / "projects" / str(project_id)).resolve()
    expected = (DATA_DIR / "projects").resolve()
    if expected not in root.parents:
        raise RuntimeError("Chemin projet hors périmètre")
    root.mkdir(parents=True, exist_ok=True)
    return root


def files_for_sync(project_id: uuid.UUID, include_paths: list[str]) -> dict[str, bytes]:
    root = project_root(project_id)
    result: dict[str, bytes] = {}
    for configured in include_paths:
        rel = safe_repo_path(configured)
        target = (root / rel).resolve()
        if root != target and root not in target.parents:
            continue
        if target.is_file():
            result[rel] = target.read_bytes()
        elif target.is_dir():
            for file in target.rglob("*"):
                if not file.is_file() or file.is_symlink():
                    continue
                relative = file.relative_to(root).as_posix()
                if any(part in {".git", "secrets", "credentials", "__pycache__"} for part in file.parts):
                    continue
                if file.stat().st_size > 25_000_000:
                    continue
                result[safe_repo_path(relative)] = file.read_bytes()
    return result


def fingerprint(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(files[path]).digest())
    return digest.hexdigest()


class UserProfileCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    github_login: str = Field(min_length=1, max_length=39, pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
    token_env_name: str = Field(min_length=18, max_length=100)
    enabled: bool = True


class ProjectSyncSettings(BaseModel):
    user_profile_id: uuid.UUID
    repository_owner: str = Field(min_length=1, max_length=39, pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
    repository_name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    branch: str = Field(default="main", min_length=1, max_length=200)
    direction: str = Field(default="bidirectional")
    conflict_policy: str = Field(default="stop")
    enabled: bool = False
    interval_minutes: int = Field(default=60, ge=15, le=43200)
    include_paths: list[str] = Field(default_factory=lambda: ["scripts", "docs", "exports"], max_length=50)
    remote_prefix: str = Field(default="hdp", max_length=200)


@router.on_event("startup")
def startup_schema() -> None:
    ensure_schema()


@router.get("/users")
def list_users() -> list[dict[str, Any]]:
    ensure_schema()
    with db() as connection:
        rows = connection.execute(
            "SELECT id, display_name, github_login, token_env_name, enabled, created_at, updated_at FROM github_user_profiles ORDER BY display_name"
        ).fetchall()
    return [
        {
            "id": str(r[0]), "display_name": r[1], "github_login": r[2],
            "credential_configured": bool(os.getenv(r[3], "").strip()),
            "token_env_name": r[3], "enabled": r[4], "created_at": r[5], "updated_at": r[6],
        }
        for r in rows
    ]


@router.post("/users")
def create_user(payload: UserProfileCreate) -> dict[str, Any]:
    ensure_schema()
    try:
        env_name = validate_token_env_name(payload.token_env_name)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    now = utcnow(); profile_id = uuid.uuid4()
    with db() as connection:
        connection.execute(
            "INSERT INTO github_user_profiles (id,display_name,github_login,token_env_name,enabled,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (profile_id, payload.display_name.strip(), payload.github_login.strip(), env_name, payload.enabled, now, now),
        )
    return {"id": str(profile_id), "credential_configured": bool(os.getenv(env_name, "").strip())}


@router.put("/projects/{project_id}")
def configure_project(project_id: uuid.UUID, payload: ProjectSyncSettings) -> dict[str, Any]:
    ensure_schema()
    if payload.direction not in SYNC_DIRECTIONS:
        raise HTTPException(422, "Sens de synchronisation invalide")
    if payload.conflict_policy not in CONFLICT_POLICIES:
        raise HTTPException(422, "Politique de conflit invalide")
    try:
        paths = [safe_repo_path(p) for p in payload.include_paths]
        prefix = safe_repo_path(payload.remote_prefix) if payload.remote_prefix else ""
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    now = utcnow()
    with db() as connection:
        if not connection.execute("SELECT 1 FROM projects WHERE id=%s AND archived_at IS NULL", (project_id,)).fetchone():
            raise HTTPException(404, "Projet introuvable")
        if not connection.execute("SELECT 1 FROM github_user_profiles WHERE id=%s AND enabled", (payload.user_profile_id,)).fetchone():
            raise HTTPException(404, "Profil GitHub utilisateur introuvable ou désactivé")
        connection.execute(
            """
            INSERT INTO project_github_sync
              (project_id,user_profile_id,repository_owner,repository_name,branch,direction,conflict_policy,enabled,interval_minutes,include_paths,remote_prefix,created_at,updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (project_id) DO UPDATE SET
              user_profile_id=EXCLUDED.user_profile_id, repository_owner=EXCLUDED.repository_owner,
              repository_name=EXCLUDED.repository_name, branch=EXCLUDED.branch,
              direction=EXCLUDED.direction, conflict_policy=EXCLUDED.conflict_policy,
              enabled=EXCLUDED.enabled, interval_minutes=EXCLUDED.interval_minutes,
              include_paths=EXCLUDED.include_paths, remote_prefix=EXCLUDED.remote_prefix,
              updated_at=EXCLUDED.updated_at
            """,
            (project_id,payload.user_profile_id,payload.repository_owner,payload.repository_name,payload.branch,payload.direction,payload.conflict_policy,payload.enabled,payload.interval_minutes,Jsonb(paths),prefix,now,now),
        )
    return {"project_id": str(project_id), "configured": True, "enabled": payload.enabled}


def load_sync_config(project_id: uuid.UUID) -> dict[str, Any]:
    ensure_schema()
    with db() as connection:
        row = connection.execute(
            """
            SELECT s.user_profile_id,s.repository_owner,s.repository_name,s.branch,s.direction,s.conflict_policy,
                   s.enabled,s.interval_minutes,s.include_paths,s.remote_prefix,s.last_local_fingerprint,s.last_remote_commit,
                   u.github_login,u.token_env_name
            FROM project_github_sync s JOIN github_user_profiles u ON u.id=s.user_profile_id
            WHERE s.project_id=%s AND u.enabled
            """, (project_id,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Synchronisation GitHub non configurée")
    keys = ["user_profile_id","repository_owner","repository_name","branch","direction","conflict_policy","enabled","interval_minutes","include_paths","remote_prefix","last_local_fingerprint","last_remote_commit","github_login","token_env_name"]
    return dict(zip(keys,row,strict=True))


async def gh(client: httpx.AsyncClient, method: str, url: str, token: str, **kwargs: Any) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    response = await client.request(method, url, headers=headers, **kwargs)
    if response.status_code >= 400:
        detail = response.text[:500]
        raise HTTPException(502, f"GitHub {response.status_code}: {detail}")
    return response


async def remote_head(client: httpx.AsyncClient, cfg: dict[str, Any], token: str) -> str | None:
    owner, repo, branch = cfg["repository_owner"], cfg["repository_name"], cfg["branch"]
    response = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/git/ref/heads/{branch}", headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise HTTPException(502, f"GitHub {response.status_code}: {response.text[:500]}")
    return str(response.json()["object"]["sha"])


@router.post("/projects/{project_id}/run")
async def run_sync(project_id: uuid.UUID) -> dict[str, Any]:
    """Exécute une itération de synchronisation avec détection de conflit.

    Cette première implémentation qualifiée effectue le contrôle d'identité,
    l'état du dépôt, l'empreinte locale et la détection de divergence. Les
    mutations GitHub sont volontairement refusées tant que la stratégie de
    commit atomique n'est pas activée dans une version ultérieure.
    """
    cfg = load_sync_config(project_id)
    if not cfg["enabled"]:
        raise HTTPException(409, "Synchronisation désactivée pour ce projet")
    token = token_for_profile(cfg)
    local_files = files_for_sync(project_id, list(cfg["include_paths"] or []))
    local_fp = fingerprint(local_files)
    run_id = uuid.uuid4(); started = utcnow()
    async with httpx.AsyncClient(timeout=30, follow_redirects=False, trust_env=False) as client:
        user = await gh(client, "GET", f"{GITHUB_API}/user", token)
        authenticated = str(user.json().get("login") or "")
        if authenticated.casefold() != str(cfg["github_login"]).casefold():
            raise HTTPException(403, "Le jeton GitHub ne correspond pas au profil utilisateur sélectionné")
        head = await remote_head(client, cfg, token)

    local_changed = bool(cfg["last_local_fingerprint"] and cfg["last_local_fingerprint"] != local_fp)
    remote_changed = bool(cfg["last_remote_commit"] and cfg["last_remote_commit"] != head)
    conflict = bool(local_changed and remote_changed and cfg["direction"] == "bidirectional")
    status = "conflict" if conflict else "ready"
    message = "Conflit détecté: modifications locales et distantes depuis la dernière synchronisation." if conflict else "État vérifié; prêt pour synchronisation atomique."
    finished = utcnow()
    with db() as connection:
        connection.execute(
            """
            INSERT INTO github_sync_runs
              (id,project_id,user_profile_id,started_at,finished_at,status,direction,remote_commit_before,
               local_fingerprint_before,local_fingerprint_after,changed_files,conflicts,message)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (run_id,project_id,cfg["user_profile_id"],started,finished,status,cfg["direction"],head,cfg["last_local_fingerprint"],local_fp,Jsonb(sorted(local_files)),Jsonb(["simultaneous_change"] if conflict else []),message),
        )
        if not conflict:
            connection.execute(
                "UPDATE project_github_sync SET last_local_fingerprint=%s,last_remote_commit=%s,last_sync_at=%s,updated_at=%s WHERE project_id=%s",
                (local_fp,head,finished,finished,project_id),
            )
    return {
        "run_id": str(run_id), "project_id": str(project_id), "github_user": authenticated,
        "repository": f"{cfg['repository_owner']}/{cfg['repository_name']}", "branch": cfg["branch"],
        "direction": cfg["direction"], "status": status, "local_file_count": len(local_files),
        "local_fingerprint": local_fp, "remote_commit": head, "conflict": conflict,
        "mutation_enabled": False, "message": message,
    }
