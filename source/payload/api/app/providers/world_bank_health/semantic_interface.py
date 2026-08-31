from __future__ import annotations

"""World Bank provider-facing bridge to the canonical HDP V7 semantic router.

The bridge does not implement a second semantic engine. It constrains the canonical
semantic request to `world-bank-health`, preserving one source of truth for intent,
geography mapping, completeness, project context, provenance and anti-false-zero.
"""

import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...v6_semantic_api import DEFAULT_PROJECT_ID, SemanticSearchRequest, semantic_plan, semantic_search
from .parameters import SEMANTIC_PARAMETER_MAPPING, parameter_documentation

router = APIRouter(
    prefix="/api/providers/world-bank-health",
    tags=["provider-world-bank-health-semantic"],
)


class WorldBankSemanticRequest(BaseModel):
    project_id: uuid.UUID = DEFAULT_PROJECT_ID
    query: str = Field(default="", max_length=200, description="Theme/keywords; never interpreted as an indicator code without catalogue evidence.")
    location: str = Field(default="", max_length=160, description="Human geography expression, e.g. Rwanda, RWA or an HDP-supported M49 value.")
    date_from: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    date_to: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    result_limit: int = Field(default=25, ge=1, le=100)

    def canonical_payload(self) -> SemanticSearchRequest:
        return SemanticSearchRequest(
            project_id=self.project_id,
            sources=["world-bank-health"],
            query=self.query,
            location=self.location,
            date_from=self.date_from,
            date_to=self.date_to,
            result_limit=self.result_limit,
        )


@router.get("/parameters")
def documented_parameters() -> dict[str, Any]:
    """Return documented native/provider parameters with explicit HDP qualification status."""
    return parameter_documentation()


@router.get("/semantic-contract")
def semantic_contract() -> dict[str, Any]:
    """Describe, without executing, the provider-facing contract to the semantic router."""
    return {
        "provider": "world-bank-health",
        "canonical_router": {
            "plan": "/api/semantic/plan",
            "search": "/api/semantic/search",
            "ui": "/api/semantic/ui",
        },
        "provider_bridge": {
            "plan": "/api/providers/world-bank-health/semantic/plan",
            "search": "/api/providers/world-bank-health/semantic/search",
        },
        "fixed_sources": ["world-bank-health"],
        "canonical_fields": ["project_id", "query", "location", "date_from", "date_to", "result_limit"],
        "mapping": SEMANTIC_PARAMETER_MAPPING,
        "invariants": {
            "project_id_is_never_sent_to_world_bank": True,
            "location_never_overwrites_project_id": True,
            "indicator_codes_require_catalogue_evidence": True,
            "world_bank_aggregates_are_not_sovereign_countries": True,
            "bounded_empty_result_is_not_provider_wide_absence": True,
            "semantic_execution_uses_reference_world_bank_service": True,
        },
    }


@router.post("/semantic/plan")
def provider_semantic_plan(payload: WorldBankSemanticRequest) -> dict[str, Any]:
    """Build the canonical HDP semantic plan constrained to World Bank Health."""
    return semantic_plan(payload.canonical_payload())


@router.post("/semantic/search")
async def provider_semantic_search(payload: WorldBankSemanticRequest) -> dict[str, Any]:
    """Execute through the canonical semantic router, not through a duplicate provider path."""
    return await semantic_search(payload.canonical_payload())
