"""Passerelle REST GitHub locale de Humanitarian Data Platform.

Le jeton reste côté serveur. Les lectures sont disponibles par défaut ; les
deux écritures exposées nécessitent GITHUB_API_WRITE_ENABLED=true. Le service
est lié à 127.0.0.1 par Docker Compose et n'est pas un proxy GitHub générique.
"""
from __future__ import annotations

import os
import re
from collections.abc import Collection
from typing import Any, Literal
from urllib.parse import quote

import httpx
from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field


APP_VERSION = "4.0.0"
API_URL = "https://api.github.com"
API_VERSION = os.getenv("GITHUB_API_VERSION", "2026-03-10").strip()
TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
DEFAULT_OWNER = os.getenv("GITHUB_DEFAULT_OWNER", "B-DAUTRIF").strip()
DEFAULT_REPO = os.getenv(
    "GITHUB_DEFAULT_REPOSITORY", "humanitarian-data-platform"
).strip()
WRITE_ENABLED = os.getenv("GITHUB_API_WRITE_ENABLED", "false").lower() in {
    "1", "true", "yes", "on",
}
TIMEOUT_SECONDS = min(
    120.0, max(1.0, float(os.getenv("GITHUB_API_TIMEOUT_SECONDS", "20")))
)
OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
WORKFLOW_RE = re.compile(r"^[A-Za-z0-9_.-]{1,255}$")

app = FastAPI(
    title="HDP GitHub API",
    version=APP_VERSION,
    description="Passerelle locale et bornée vers les fonctions REST GitHub utilisées par HDP.",
)


class IssueCreate(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    body: str = Field(default="", max_length=65_536)
    labels: list[str] = Field(default_factory=list, max_length=20)


class WorkflowDispatch(BaseModel):
    ref: str = Field(min_length=1, max_length=255)
    inputs: dict[str, str] = Field(default_factory=dict)


def repository(owner: str | None, repo: str | None) -> tuple[str, str]:
    normalized_owner = (owner or DEFAULT_OWNER).strip()
    normalized_repo = (repo or DEFAULT_REPO).strip()
    if not OWNER_RE.fullmatch(normalized_owner):
        raise HTTPException(422, "Propriétaire GitHub invalide.")
    if not REPO_RE.fullmatch(normalized_repo) or normalized_repo in {".", ".."}:
        raise HTTPException(422, "Nom de dépôt GitHub invalide.")
    return normalized_owner, normalized_repo


def github_headers() -> dict[str, str]:
    values = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": f"HumanitarianDataPlatform/{APP_VERSION}",
    }
    if TOKEN:
        values["Authorization"] = f"Bearer {TOKEN}"
    return values


def safe_error_detail(response: httpx.Response) -> Any:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            return payload.get("message", "GitHub a refusé la requête.")
        return "GitHub a refusé la requête."
    except ValueError:
        return response.text[:500] or "Réponse GitHub inattendue."


async def github_request(
    method: Literal["GET", "POST"],
    endpoint: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    expected: Collection[int] = (200,),
) -> tuple[Any, httpx.Headers]:
    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT_SECONDS, follow_redirects=False
        ) as client:
            response = await client.request(
                method,
                API_URL + endpoint,
                headers=github_headers(),
                params=params,
                json=body,
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(504, "Délai GitHub dépassé.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(502, "Erreur réseau GitHub.") from exc
    if response.status_code not in expected:
        raise HTTPException(response.status_code, safe_error_detail(response))
    if response.status_code == 204 or not response.content:
        return None, response.headers
    try:
        return response.json(), response.headers
    except ValueError as exc:
        raise HTTPException(502, "Réponse GitHub non JSON inattendue.") from exc


def response_metadata(headers: httpx.Headers) -> dict[str, str | None]:
    return {
        key: headers.get(key)
        for key in (
            "link", "x-ratelimit-limit", "x-ratelimit-remaining",
            "x-ratelimit-reset", "x-ratelimit-used",
        )
    }


def require_write() -> None:
    if not WRITE_ENABLED:
        raise HTTPException(403, "Écritures GitHub désactivées côté serveur.")
    if not TOKEN:
        raise HTTPException(503, "GITHUB_TOKEN requis.")


async def paged(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    data, headers = await github_request("GET", endpoint, params=params)
    return {"items": data, "meta": response_metadata(headers)}


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": APP_VERSION,
        "github_api_version": API_VERSION,
        "token_configured": bool(TOKEN),
        "write_enabled": WRITE_ENABLED,
    }


@app.get("/repository")
async def get_repository(owner: str | None = None, repo: str | None = None) -> Any:
    owner, repo = repository(owner, repo)
    data, _ = await github_request("GET", f"/repos/{owner}/{repo}")
    return data


@app.get("/branches")
async def branches(
    owner: str | None = None,
    repo: str | None = None,
    per_page: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
) -> dict[str, Any]:
    owner, repo = repository(owner, repo)
    return await paged(
        f"/repos/{owner}/{repo}/branches", {"per_page": per_page, "page": page}
    )


@app.get("/commits")
async def commits(
    owner: str | None = None,
    repo: str | None = None,
    sha: str | None = None,
    per_page: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
) -> dict[str, Any]:
    owner, repo = repository(owner, repo)
    params: dict[str, Any] = {"per_page": per_page, "page": page}
    if sha:
        params["sha"] = sha[:255]
    return await paged(f"/repos/{owner}/{repo}/commits", params)


@app.get("/issues")
async def issues(
    owner: str | None = None,
    repo: str | None = None,
    state: Literal["open", "closed", "all"] = "open",
    per_page: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
) -> dict[str, Any]:
    owner, repo = repository(owner, repo)
    return await paged(
        f"/repos/{owner}/{repo}/issues",
        {"state": state, "per_page": per_page, "page": page},
    )


@app.get("/pulls")
async def pulls(
    owner: str | None = None,
    repo: str | None = None,
    state: Literal["open", "closed", "all"] = "open",
    per_page: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
) -> dict[str, Any]:
    owner, repo = repository(owner, repo)
    return await paged(
        f"/repos/{owner}/{repo}/pulls",
        {"state": state, "per_page": per_page, "page": page},
    )


@app.get("/releases")
async def releases(
    owner: str | None = None,
    repo: str | None = None,
    per_page: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
) -> dict[str, Any]:
    owner, repo = repository(owner, repo)
    return await paged(
        f"/repos/{owner}/{repo}/releases", {"per_page": per_page, "page": page}
    )


@app.get("/workflows")
async def workflows(
    owner: str | None = None,
    repo: str | None = None,
    per_page: int = Query(30, ge=1, le=100),
    page: int = Query(1, ge=1),
) -> Any:
    owner, repo = repository(owner, repo)
    data, _ = await github_request(
        "GET",
        f"/repos/{owner}/{repo}/actions/workflows",
        params={"per_page": per_page, "page": page},
    )
    return data


@app.get("/contents/{content_path:path}")
async def contents(
    content_path: str,
    owner: str | None = None,
    repo: str | None = None,
    ref: str | None = None,
) -> Any:
    owner, repo = repository(owner, repo)
    clean = "/".join(
        quote(part, safe="")
        for part in content_path.strip("/").split("/")
        if part
    )
    endpoint = f"/repos/{owner}/{repo}/contents" + (f"/{clean}" if clean else "")
    data, _ = await github_request(
        "GET", endpoint, params={"ref": ref[:255]} if ref else None
    )
    return data


@app.get("/rate-limit")
async def rate_limit() -> Any:
    data, _ = await github_request("GET", "/rate_limit")
    return data


@app.post("/issues", status_code=201)
async def create_issue(
    payload: IssueCreate,
    owner: str | None = None,
    repo: str | None = None,
) -> Any:
    require_write()
    owner, repo = repository(owner, repo)
    body: dict[str, Any] = {"title": payload.title, "body": payload.body}
    if payload.labels:
        body["labels"] = payload.labels
    data, _ = await github_request(
        "POST", f"/repos/{owner}/{repo}/issues", body=body, expected=(201,)
    )
    return data


@app.post("/workflows/{workflow_id}/dispatch", status_code=204)
async def dispatch_workflow(
    workflow_id: str,
    payload: WorkflowDispatch,
    owner: str | None = None,
    repo: str | None = None,
) -> Response:
    require_write()
    if not WORKFLOW_RE.fullmatch(workflow_id):
        raise HTTPException(422, "Identifiant de workflow invalide.")
    owner, repo = repository(owner, repo)
    await github_request(
        "POST",
        f"/repos/{owner}/{repo}/actions/workflows/{quote(workflow_id, safe='')}/dispatches",
        body={"ref": payload.ref, "inputs": payload.inputs},
        expected=(204,),
    )
    return Response(status_code=204)
