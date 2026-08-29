from __future__ import annotations

"""Synchronisation GitHub automatisée par utilisateur et par projet pour HDP.

Sécurité et comportement:
- aucun jeton GitHub en base: seulement le nom d'une variable d'environnement;
- dépôt/branche/sens/chemins/fréquence configurés par projet;
- commits distants créés atomiquement avec Git Data API;
- aucune suppression distante ou locale implicite;
- conflit par défaut si local et distant ont évolué depuis le dernier point commun;
- journal d'audit complet par exécution.
"""

import asyncio
import base64
import hashlib
import os
import re
import uuid
from contextlib import suppress
from datetime import UTC, datetime, timedelta
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
OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
BRANCH_RE = re.compile(r"^(?!/)(?!.*//)(?!.*\.\.)(?!.*@$)(?!.*[~^:?*\[\\])[A-Za-z0-9._/-]{1,200}$")
SAFE_REPO_PATH = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/@+ -]{1,500}$")
MAX_SYNC_FILE_BYTES = 25_000_000
MAX_SYNC_FILES = 5000
SCHEDULER_POLL_SECONDS = 60

router = APIRouter(prefix="/api/github-sync", tags=["GitHub sync"])
_scheduler_task: asyncio.Task[None] | None = None


def db() -> psycopg.Connection[Any]:
    return psycopg.connect(DATABASE_URL, autocommit=True)


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_schema() -> None:
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
                action TEXT NOT NULL DEFAULT 'check',
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
        connection.execute("ALTER TABLE github_sync_runs ADD COLUMN IF NOT EXISTS action TEXT NOT NULL DEFAULT 'check'")


def validate_token_env_name(value: str) -> str:
    name = value.strip().upper()
    if not TOKEN_ENV_RE.fullmatch(name):
        raise ValueError("Nom de secret attendu: HDP_GITHUB_TOKEN_<UTILISATEUR>")
    return name


def validate_owner(value: str) -> str:
    value = value.strip()
    if not OWNER_RE.fullmatch(value):
        raise ValueError("Propriétaire GitHub invalide")
    return value


def validate_repo(value: str) -> str:
    value = value.strip()
    if not REPO_RE.fullmatch(value) or value in {".", ".."}:
        raise ValueError("Nom de dépôt GitHub invalide")
    return value


def validate_branch(value: str) -> str:
    value = value.strip()
    if not BRANCH_RE.fullmatch(value):
        raise ValueError("Nom de branche GitHub invalide")
    return value


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
        candidates = [target] if target.is_file() else list(target.rglob("*")) if target.is_dir() else []
        for file in candidates:
            if not file.is_file() or file.is_symlink():
                continue
            relative = file.relative_to(root).as_posix()
            if any(part in {".git", "secrets", "credentials", "__pycache__"} for part in file.relative_to(root).parts):
                continue
            if file.stat().st_size > MAX_SYNC_FILE_BYTES:
                continue
            result[safe_repo_path(relative)] = file.read_bytes()
            if len(result) > MAX_SYNC_FILES:
                raise HTTPException(413, f"Synchronisation limitée à {MAX_SYNC_FILES} fichiers")
    return result


def fingerprint(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.encode("utf-8")); digest.update(b"\0")
        digest.update(hashlib.sha256(files[path]).digest())
    return digest.hexdigest()


def remote_project_prefix(cfg: dict[str, Any], project_id: uuid.UUID) -> str:
    base = str(cfg.get("remote_prefix") or "").strip("/")
    return safe_repo_path(f"{base}/{project_id}" if base else str(project_id))


class UserProfileCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    github_login: str = Field(min_length=1, max_length=39)
    token_env_name: str = Field(min_length=18, max_length=100)
    enabled: bool = True


class UserProfilePatch(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    github_login: str | None = Field(default=None, min_length=1, max_length=39)
    token_env_name: str | None = Field(default=None, min_length=18, max_length=100)
    enabled: bool | None = None


class ProjectSyncSettings(BaseModel):
    user_profile_id: uuid.UUID
    repository_owner: str = Field(min_length=1, max_length=39)
    repository_name: str = Field(min_length=1, max_length=100)
    branch: str = Field(default="main", min_length=1, max_length=200)
    direction: str = Field(default="bidirectional")
    conflict_policy: str = Field(default="stop")
    enabled: bool = False
    interval_minutes: int = Field(default=60, ge=15, le=43200)
    include_paths: list[str] = Field(default_factory=lambda: ["scripts", "docs", "exports"], max_length=50)
    remote_prefix: str = Field(default="hdp", max_length=200)


def profile_dict(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "id": str(row[0]), "display_name": row[1], "github_login": row[2],
        "token_env_name": row[3], "credential_configured": bool(os.getenv(row[3], "").strip()),
        "enabled": row[4], "created_at": row[5], "updated_at": row[6],
    }


@router.get("/users")
def list_users() -> list[dict[str, Any]]:
    ensure_schema()
    with db() as connection:
        rows = connection.execute(
            "SELECT id,display_name,github_login,token_env_name,enabled,created_at,updated_at FROM github_user_profiles ORDER BY display_name"
        ).fetchall()
    return [profile_dict(r) for r in rows]


@router.post("/users")
def create_user(payload: UserProfileCreate) -> dict[str, Any]:
    ensure_schema()
    try:
        login = validate_owner(payload.github_login)
        env_name = validate_token_env_name(payload.token_env_name)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    now = utcnow(); profile_id = uuid.uuid4()
    with db() as connection:
        connection.execute(
            "INSERT INTO github_user_profiles (id,display_name,github_login,token_env_name,enabled,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (profile_id,payload.display_name.strip(),login,env_name,payload.enabled,now,now),
        )
    return {"id": str(profile_id), "credential_configured": bool(os.getenv(env_name, "").strip())}


@router.patch("/users/{profile_id}")
def update_user(profile_id: uuid.UUID, payload: UserProfilePatch) -> dict[str, Any]:
    ensure_schema(); updates: dict[str, Any] = {}
    try:
        if payload.display_name is not None: updates["display_name"] = payload.display_name.strip()
        if payload.github_login is not None: updates["github_login"] = validate_owner(payload.github_login)
        if payload.token_env_name is not None: updates["token_env_name"] = validate_token_env_name(payload.token_env_name)
        if payload.enabled is not None: updates["enabled"] = payload.enabled
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not updates: return {"id": str(profile_id), "updated": False}
    updates["updated_at"] = utcnow()
    assignments = ",".join(f"{key}=%s" for key in updates)
    with db() as connection:
        result = connection.execute(f"UPDATE github_user_profiles SET {assignments} WHERE id=%s", (*updates.values(), profile_id))
        if result.rowcount != 1: raise HTTPException(404, "Profil GitHub introuvable")
    return {"id": str(profile_id), "updated": True}


@router.put("/projects/{project_id}")
def configure_project(project_id: uuid.UUID, payload: ProjectSyncSettings) -> dict[str, Any]:
    ensure_schema()
    if payload.direction not in SYNC_DIRECTIONS: raise HTTPException(422, "Sens de synchronisation invalide")
    if payload.conflict_policy not in CONFLICT_POLICIES: raise HTTPException(422, "Politique de conflit invalide")
    try:
        owner = validate_owner(payload.repository_owner); repo = validate_repo(payload.repository_name); branch = validate_branch(payload.branch)
        paths = [safe_repo_path(p) for p in payload.include_paths]
        prefix = safe_repo_path(payload.remote_prefix) if payload.remote_prefix else ""
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    now = utcnow(); next_run = now + timedelta(minutes=payload.interval_minutes) if payload.enabled else None
    with db() as connection:
        if not connection.execute("SELECT 1 FROM projects WHERE id=%s AND archived_at IS NULL", (project_id,)).fetchone():
            raise HTTPException(404, "Projet introuvable")
        if not connection.execute("SELECT 1 FROM github_user_profiles WHERE id=%s AND enabled", (payload.user_profile_id,)).fetchone():
            raise HTTPException(404, "Profil GitHub utilisateur introuvable ou désactivé")
        connection.execute(
            """
            INSERT INTO project_github_sync
              (project_id,user_profile_id,repository_owner,repository_name,branch,direction,conflict_policy,enabled,interval_minutes,include_paths,remote_prefix,next_sync_at,created_at,updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (project_id) DO UPDATE SET
              user_profile_id=EXCLUDED.user_profile_id,repository_owner=EXCLUDED.repository_owner,
              repository_name=EXCLUDED.repository_name,branch=EXCLUDED.branch,direction=EXCLUDED.direction,
              conflict_policy=EXCLUDED.conflict_policy,enabled=EXCLUDED.enabled,interval_minutes=EXCLUDED.interval_minutes,
              include_paths=EXCLUDED.include_paths,remote_prefix=EXCLUDED.remote_prefix,next_sync_at=EXCLUDED.next_sync_at,
              updated_at=EXCLUDED.updated_at
            """,
            (project_id,payload.user_profile_id,owner,repo,branch,payload.direction,payload.conflict_policy,payload.enabled,payload.interval_minutes,Jsonb(paths),prefix,next_run,now,now),
        )
    return {"project_id": str(project_id), "configured": True, "enabled": payload.enabled, "next_sync_at": next_run}


@router.get("/projects/{project_id}")
def project_status(project_id: uuid.UUID) -> dict[str, Any]:
    cfg = load_sync_config(project_id)
    return {k:(str(v) if isinstance(v, uuid.UUID) else v) for k,v in cfg.items() if k != "token_env_name"} | {
        "credential_configured": bool(os.getenv(str(cfg["token_env_name"]), "").strip())
    }


@router.get("/projects/{project_id}/runs")
def project_runs(project_id: uuid.UUID, limit: int = 50) -> list[dict[str, Any]]:
    ensure_schema(); limit = max(1, min(limit, 200))
    with db() as connection:
        rows = connection.execute(
            "SELECT id,started_at,finished_at,status,direction,action,remote_commit_before,remote_commit_after,local_fingerprint_before,local_fingerprint_after,changed_files,conflicts,message FROM github_sync_runs WHERE project_id=%s ORDER BY started_at DESC LIMIT %s",
            (project_id,limit),
        ).fetchall()
    keys=["id","started_at","finished_at","status","direction","action","remote_commit_before","remote_commit_after","local_fingerprint_before","local_fingerprint_after","changed_files","conflicts","message"]
    return [dict(zip(keys,r,strict=True)) | {"id":str(r[0])} for r in rows]


def load_sync_config(project_id: uuid.UUID) -> dict[str, Any]:
    ensure_schema()
    with db() as connection:
        row = connection.execute(
            """
            SELECT s.user_profile_id,s.repository_owner,s.repository_name,s.branch,s.direction,s.conflict_policy,
                   s.enabled,s.interval_minutes,s.include_paths,s.remote_prefix,s.last_local_fingerprint,s.last_remote_commit,
                   s.last_sync_at,s.next_sync_at,u.github_login,u.token_env_name
            FROM project_github_sync s JOIN github_user_profiles u ON u.id=s.user_profile_id
            WHERE s.project_id=%s AND u.enabled
            """, (project_id,)
        ).fetchone()
    if not row: raise HTTPException(404, "Synchronisation GitHub non configurée")
    keys=["user_profile_id","repository_owner","repository_name","branch","direction","conflict_policy","enabled","interval_minutes","include_paths","remote_prefix","last_local_fingerprint","last_remote_commit","last_sync_at","next_sync_at","github_login","token_env_name"]
    return dict(zip(keys,row,strict=True))


def headers(token: str) -> dict[str, str]:
    return {"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"HDP-GitHub-Sync/6.0"}


async def gh(client: httpx.AsyncClient, method: str, url: str, token: str, **kwargs: Any) -> httpx.Response:
    response = await client.request(method,url,headers=headers(token),**kwargs)
    if response.status_code >= 400:
        raise HTTPException(502,f"GitHub {response.status_code}: {response.text[:500]}")
    return response


async def authenticated_login(client: httpx.AsyncClient, token: str) -> str:
    response = await gh(client,"GET",f"{GITHUB_API}/user",token)
    return str(response.json().get("login") or "")


async def remote_head(client: httpx.AsyncClient, cfg: dict[str, Any], token: str) -> str | None:
    owner,repo,branch=cfg["repository_owner"],cfg["repository_name"],cfg["branch"]
    response=await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/git/ref/heads/{branch}",headers=headers(token))
    if response.status_code==404: return None
    if response.status_code>=400: raise HTTPException(502,f"GitHub {response.status_code}: {response.text[:500]}")
    return str(response.json()["object"]["sha"])


async def get_commit_tree(client: httpx.AsyncClient,cfg:dict[str,Any],token:str,commit_sha:str) -> str:
    owner,repo=cfg["repository_owner"],cfg["repository_name"]
    response=await gh(client,"GET",f"{GITHUB_API}/repos/{owner}/{repo}/git/commits/{commit_sha}",token)
    return str(response.json()["tree"]["sha"])


async def push_files(client:httpx.AsyncClient,cfg:dict[str,Any],project_id:uuid.UUID,token:str,local_files:dict[str,bytes],head:str|None) -> tuple[str,list[str]]:
    if head is None:
        raise HTTPException(409,"La branche distante n'existe pas; créez d'abord le dépôt et sa branche initiale")
    owner,repo,branch=cfg["repository_owner"],cfg["repository_name"],cfg["branch"]
    base_tree=await get_commit_tree(client,cfg,token,head)
    prefix=remote_project_prefix(cfg,project_id)
    tree_entries=[]; changed=[]
    for rel,data in sorted(local_files.items()):
        blob=await gh(client,"POST",f"{GITHUB_API}/repos/{owner}/{repo}/git/blobs",token,json={"content":base64.b64encode(data).decode("ascii"),"encoding":"base64"})
        tree_entries.append({"path":f"{prefix}/{rel}","mode":"100644","type":"blob","sha":blob.json()["sha"]}); changed.append(rel)
    if not tree_entries: return head,[]
    tree=await gh(client,"POST",f"{GITHUB_API}/repos/{owner}/{repo}/git/trees",token,json={"base_tree":base_tree,"tree":tree_entries})
    message=f"chore(hdp): sync project {project_id}"
    commit=await gh(client,"POST",f"{GITHUB_API}/repos/{owner}/{repo}/git/commits",token,json={"message":message,"tree":tree.json()["sha"],"parents":[head]})
    new_sha=str(commit.json()["sha"])
    ref=await client.patch(f"{GITHUB_API}/repos/{owner}/{repo}/git/refs/heads/{branch}",headers=headers(token),json={"sha":new_sha,"force":False})
    if ref.status_code>=400:
        raise HTTPException(409,"Le dépôt a changé pendant le push; synchronisation arrêtée pour éviter un écrasement")
    return new_sha,changed


async def remote_files(client:httpx.AsyncClient,cfg:dict[str,Any],project_id:uuid.UUID,token:str,head:str) -> dict[str,bytes]:
    owner,repo=cfg["repository_owner"],cfg["repository_name"]
    tree_sha=await get_commit_tree(client,cfg,token,head)
    tree=await gh(client,"GET",f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1",token)
    if tree.json().get("truncated"):
        raise HTTPException(413,"Arborescence GitHub trop volumineuse/tronquée")
    prefix=remote_project_prefix(cfg,project_id)+"/"
    files:dict[str,bytes]={}
    for item in tree.json().get("tree",[]):
        path=str(item.get("path") or "")
        if item.get("type")!="blob" or not path.startswith(prefix): continue
        rel=safe_repo_path(path[len(prefix):])
        size=int(item.get("size") or 0)
        if size>MAX_SYNC_FILE_BYTES: continue
        blob=await gh(client,"GET",f"{GITHUB_API}/repos/{owner}/{repo}/git/blobs/{item['sha']}",token)
        if blob.json().get("encoding")!="base64": raise HTTPException(502,"Encodage de blob GitHub inattendu")
        files[rel]=base64.b64decode(str(blob.json().get("content") or "").replace("\n",""),validate=True)
        if len(files)>MAX_SYNC_FILES: raise HTTPException(413,f"Synchronisation limitée à {MAX_SYNC_FILES} fichiers")
    return files


def write_remote_files(project_id:uuid.UUID,files:dict[str,bytes]) -> list[str]:
    root=project_root(project_id); written=[]
    for rel,data in sorted(files.items()):
        destination=(root/safe_repo_path(rel)).resolve()
        if root not in destination.parents: raise HTTPException(400,"Chemin distant hors projet")
        destination.parent.mkdir(parents=True,exist_ok=True)
        tmp=destination.with_name(destination.name+f".hdp-sync-{uuid.uuid4().hex}.tmp")
        tmp.write_bytes(data); os.replace(tmp,destination); written.append(rel)
    return written


def audit_run(project_id:uuid.UUID,cfg:dict[str,Any],started:datetime,status:str,action:str,head_before:str|None,head_after:str|None,local_before:str|None,local_after:str|None,changed:list[str],conflicts:list[str],message:str) -> str:
    run_id=uuid.uuid4(); finished=utcnow()
    with db() as connection:
        connection.execute(
            """
            INSERT INTO github_sync_runs
              (id,project_id,user_profile_id,started_at,finished_at,status,direction,action,remote_commit_before,remote_commit_after,local_fingerprint_before,local_fingerprint_after,changed_files,conflicts,message)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (run_id,project_id,cfg["user_profile_id"],started,finished,status,cfg["direction"],action,head_before,head_after,local_before,local_after,Jsonb(changed),Jsonb(conflicts),message),
        )
        next_run=finished+timedelta(minutes=int(cfg["interval_minutes"])) if cfg["enabled"] else None
        if status=="success":
            connection.execute("UPDATE project_github_sync SET last_local_fingerprint=%s,last_remote_commit=%s,last_sync_at=%s,next_sync_at=%s,updated_at=%s WHERE project_id=%s",(local_after,head_after,finished,next_run,finished,project_id))
        else:
            connection.execute("UPDATE project_github_sync SET next_sync_at=%s,updated_at=%s WHERE project_id=%s",(next_run,finished,project_id))
    return str(run_id)


async def synchronize_project(project_id:uuid.UUID,*,manual:bool=False) -> dict[str,Any]:
    cfg=load_sync_config(project_id)
    if not cfg["enabled"] and not manual: raise HTTPException(409,"Synchronisation désactivée pour ce projet")
    token=token_for_profile(cfg); started=utcnow()
    local_files=files_for_sync(project_id,list(cfg["include_paths"] or [])); local_fp=fingerprint(local_files)
    async with httpx.AsyncClient(timeout=45,follow_redirects=False,trust_env=False) as client:
        login=await authenticated_login(client,token)
        if login.casefold()!=str(cfg["github_login"]).casefold(): raise HTTPException(403,"Le jeton GitHub ne correspond pas au profil utilisateur sélectionné")
        head=await remote_head(client,cfg,token)
        local_changed=cfg["last_local_fingerprint"] is not None and cfg["last_local_fingerprint"]!=local_fp
        remote_changed=cfg["last_remote_commit"] is not None and cfg["last_remote_commit"]!=head
        first_sync=cfg["last_local_fingerprint"] is None and cfg["last_remote_commit"] is None
        action="check"; conflicts: list[str]=[]; changed: list[str]=[]; new_head=head; new_local_fp=local_fp

        if first_sync:
            if cfg["direction"]=="push": action="push"
            elif cfg["direction"]=="pull": action="pull"
            elif head is None: action="push"
            elif not local_files: action="pull"
            else: conflicts=["initial_state_ambiguous"]
        elif cfg["direction"]=="push": action="push" if local_changed else "check"
        elif cfg["direction"]=="pull": action="pull" if remote_changed else "check"
        else:
            if local_changed and remote_changed:
                if cfg["conflict_policy"]=="prefer_local": action="push"
                elif cfg["conflict_policy"]=="prefer_remote": action="pull"
                else: conflicts=["simultaneous_change"]
            elif local_changed: action="push"
            elif remote_changed: action="pull"

        if conflicts:
            run_id=audit_run(project_id,cfg,started,"conflict","stop",head,head,cfg["last_local_fingerprint"],local_fp,[],conflicts,"Synchronisation arrêtée: divergence locale/distante.")
            return {"run_id":run_id,"status":"conflict","conflicts":conflicts,"repository":f"{cfg['repository_owner']}/{cfg['repository_name']}","branch":cfg["branch"]}

        if action=="push":
            new_head,changed=await push_files(client,cfg,project_id,token,local_files,head)
        elif action=="pull":
            if head is None: raise HTTPException(409,"Branche distante absente")
            incoming=await remote_files(client,cfg,project_id,token,head); changed=write_remote_files(project_id,incoming)
            local_files=files_for_sync(project_id,list(cfg["include_paths"] or [])); new_local_fp=fingerprint(local_files)
        message={"push":"Commit HDP créé et branche avancée.","pull":"Fichiers GitHub appliqués localement sans suppression implicite.","check":"Aucun changement à synchroniser."}[action]
        run_id=audit_run(project_id,cfg,started,"success",action,head,new_head,cfg["last_local_fingerprint"],new_local_fp,changed,[],message)
        return {"run_id":run_id,"status":"success","action":action,"github_user":login,"repository":f"{cfg['repository_owner']}/{cfg['repository_name']}","branch":cfg["branch"],"changed_files":changed,"remote_commit":new_head,"local_fingerprint":new_local_fp}


@router.post("/projects/{project_id}/run")
async def run_sync(project_id:uuid.UUID) -> dict[str,Any]:
    return await synchronize_project(project_id,manual=True)


async def scheduler_loop() -> None:
    while True:
        try:
            ensure_schema(); now=utcnow()
            with db() as connection:
                rows=connection.execute("SELECT project_id FROM project_github_sync WHERE enabled AND (next_sync_at IS NULL OR next_sync_at<=%s) ORDER BY COALESCE(next_sync_at,'1970-01-01'::timestamptz) LIMIT 20",(now,)).fetchall()
            for (project_id,) in rows:
                try:
                    await synchronize_project(project_id)
                except Exception as exc:
                    with suppress(Exception):
                        cfg=load_sync_config(project_id)
                        audit_run(project_id,cfg,utcnow(),"error","check",cfg.get("last_remote_commit"),cfg.get("last_remote_commit"),cfg.get("last_local_fingerprint"),cfg.get("last_local_fingerprint"),[],[],str(exc)[:1000])
        except Exception:
            pass
        await asyncio.sleep(SCHEDULER_POLL_SECONDS)


@router.on_event("startup")
async def start_scheduler() -> None:
    global _scheduler_task
    ensure_schema()
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task=asyncio.create_task(scheduler_loop(),name="hdp-github-sync")


@router.on_event("shutdown")
async def stop_scheduler() -> None:
    global _scheduler_task
    if _scheduler_task is not None:
        _scheduler_task.cancel()
        with suppress(asyncio.CancelledError): await _scheduler_task
        _scheduler_task=None
