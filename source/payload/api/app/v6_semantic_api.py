from __future__ import annotations

"""V6 semantic-router API.

This test-branch API executes the existing verified source connectors through a
semantic plan. Provider failures and unsupported/degraded criteria are returned per
source instead of being collapsed into an empty result set.
"""

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .federated_search import filter_catalog_items, unified_federated_items
from .health_sources import SEARCHABLE_SOURCE_IDS
from .semantic_router import build_execution_plan


router = APIRouter(prefix="/api/semantic", tags=["semantic-router"])


class SemanticSearchRequest(BaseModel):
    sources: list[str] = Field(default_factory=lambda: list(SEARCHABLE_SOURCE_IDS), min_length=1, max_length=20)
    query: str = Field(default="", max_length=200)
    location: str = Field(default="", max_length=160)
    date_from: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    date_to: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    result_limit: int = Field(default=25, ge=1, le=100)


def _validate_sources(sources: list[str]) -> list[str]:
    unique = list(dict.fromkeys(value.strip() for value in sources if value.strip()))
    invalid = [value for value in unique if value not in SEARCHABLE_SOURCE_IDS]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Sources inconnues: {', '.join(invalid)}")
    if not unique:
        raise HTTPException(status_code=422, detail="Sélectionnez au moins une source")
    return unique


@router.post("/plan")
def semantic_plan(payload: SemanticSearchRequest) -> dict[str, Any]:
    sources = _validate_sources(payload.sources)
    try:
        return build_execution_plan(
            sources,
            query=payload.query,
            location=payload.location,
            date_from=payload.date_from,
            date_to=payload.date_to,
            result_limit=payload.result_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


async def _execute_source(route: dict[str, Any]) -> dict[str, Any]:
    # Imported lazily to avoid a circular import while app.main is bootstrapping.
    from .main import get_source_global_settings, search_remote_source

    source_id = str(route["source"])
    try:
        global_configuration = get_source_global_settings(source_id)
        global_settings = global_configuration["settings"]
        if not global_settings.get("enabled", True):
            return {
                "source": source_id,
                "status": "disabled",
                "item_count": 0,
                "items": [],
                "error": "Ce connecteur est désactivé globalement",
                "route": route,
            }
        _, items = await search_remote_source(source_id, dict(route["parameters"]), global_settings)
        params = route["parameters"]
        filtered = filter_catalog_items(
            items,
            date_from=str(params.get("date_from") or ""),
            date_to=str(params.get("date_to") or ""),
            location=str(params.get("location") or ""),
        )[: int(params.get("result_limit") or 25)]
        return {
            "source": source_id,
            "status": "success",
            "item_count": len(filtered),
            "items": filtered,
            "error": None,
            "route": route,
        }
    except Exception as exc:  # Source/API failures are data, not fake empty successes.
        return {
            "source": source_id,
            "status": "error",
            "item_count": 0,
            "items": [],
            "error": f"{type(exc).__name__}: {exc}",
            "route": route,
        }


@router.post("/search")
async def semantic_search(payload: SemanticSearchRequest) -> dict[str, Any]:
    sources = _validate_sources(payload.sources)
    try:
        plan = build_execution_plan(
            sources,
            query=payload.query,
            location=payload.location,
            date_from=payload.date_from,
            date_to=payload.date_to,
            result_limit=payload.result_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    executions = await asyncio.gather(*(_execute_source(route) for route in plan["routes"]))
    successes = [entry for entry in executions if entry["status"] == "success"]
    unified = unified_federated_items((entry["source"], entry["items"]) for entry in successes)
    return {
        "status": "success" if len(successes) == len(executions) else "partial",
        "plan": plan,
        "sources": executions,
        "item_count": len(unified),
        "items": unified,
    }
