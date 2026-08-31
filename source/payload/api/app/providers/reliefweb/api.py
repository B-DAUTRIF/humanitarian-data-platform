from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..base.errors import ProviderConfigurationError, ProviderRateLimitedError, ProviderValidationError
from .descriptor import RELIEFWEB_DESCRIPTOR
from .service import ReliefWebService

router = APIRouter(prefix="/api/providers/reliefweb", tags=["provider-reliefweb"])


class ReliefWebSearchRequest(BaseModel):
    project_id: uuid.UUID | None = None
    content_type: str = Field(default="reports", max_length=40)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ReliefWebItemRequest(BaseModel):
    project_id: uuid.UUID | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


def _contexts(project_id: uuid.UUID | None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from ...main import get_project_source_settings, get_source_global_settings

    global_record = get_source_global_settings("reliefweb")
    global_settings = dict(global_record.get("settings") or {})
    project_parameters: dict[str, Any] = {}
    if project_id is not None:
        project_record = get_project_source_settings(project_id, "reliefweb")
        if not project_record.get("enabled", True):
            raise ProviderConfigurationError("ReliefWeb is disabled for this HDP project")
        project_parameters = dict(project_record.get("parameters") or {})
    runtime = dict(global_settings)
    runtime.setdefault("timeout_seconds", 20)
    runtime.setdefault("connect_timeout_seconds", 5)
    runtime.setdefault("user_agent", "HDP/7")
    runtime.setdefault("accept_language", "en")
    return runtime, global_settings, project_parameters


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ProviderConfigurationError):
        return HTTPException(status_code=503, detail={"status":"configuration_error", "message":str(exc)})
    if isinstance(exc, ProviderRateLimitedError):
        return HTTPException(status_code=429, detail={"status":"rate_limited", "message":str(exc)})
    if isinstance(exc, (ProviderValidationError, ValueError)):
        return HTTPException(status_code=422, detail={"status":"validation_error", "message":str(exc)})
    return HTTPException(status_code=502, detail={"status":"provider_error", "message":f"{type(exc).__name__}: {exc}"})


@router.get("/descriptor")
def descriptor() -> dict[str, Any]:
    return RELIEFWEB_DESCRIPTOR.to_dict()


@router.get("/configuration/effective")
def effective_configuration(project_id: uuid.UUID | None = None) -> dict[str, Any]:
    runtime, global_settings, project_parameters = _contexts(project_id)
    service = ReliefWebService(runtime)
    return {"provider":"reliefweb", "project_id":str(project_id) if project_id else None, "configuration":service.effective_configuration(global_settings=global_settings, project_settings=project_parameters)}


@router.post("/search")
async def search(payload: ReliefWebSearchRequest) -> dict[str, Any]:
    if payload.content_type not in RELIEFWEB_DESCRIPTOR.content_types:
        raise HTTPException(status_code=422, detail={"status":"validation_error", "message":f"Unknown ReliefWeb content type: {payload.content_type}"})
    try:
        runtime, global_settings, project_parameters = _contexts(payload.project_id)
        service = ReliefWebService(runtime)
        raw, normalized, native_request = await service.execute(payload.content_type, payload.parameters, global_settings=global_settings, project_settings=project_parameters)
        return {"provider":"reliefweb", "content_type":payload.content_type, "status":"success" if normalized else "empty_valid", "count":len(normalized), "items":normalized, "native_response":raw, "native_request":native_request}
    except Exception as exc:
        raise _http_error(exc) from exc


@router.post("/item/{content_type}/{item_id}")
async def item(content_type: str, item_id: str, payload: ReliefWebItemRequest) -> dict[str, Any]:
    if content_type not in RELIEFWEB_DESCRIPTOR.content_types:
        raise HTTPException(status_code=422, detail={"status":"validation_error", "message":f"Unknown ReliefWeb content type: {content_type}"})
    try:
        runtime, global_settings, project_parameters = _contexts(payload.project_id)
        service = ReliefWebService(runtime)
        raw, normalized, native_request = await service.execute(content_type, payload.parameters, global_settings=global_settings, project_settings=project_parameters, item_id=item_id)
        return {"provider":"reliefweb", "content_type":content_type, "item_id":item_id, "status":"success" if normalized else "empty_valid", "items":normalized, "native_response":raw, "native_request":native_request}
    except Exception as exc:
        raise _http_error(exc) from exc
