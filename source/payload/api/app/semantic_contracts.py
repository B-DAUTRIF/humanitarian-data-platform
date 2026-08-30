from __future__ import annotations

"""Versioned internal contracts shared by HDP semantic/acquisition contexts."""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


CONTRACT_VERSION = "7.0.0-alpha.1"


class CapabilityMode(StrEnum):
    NATIVE_FILTER = "native_filter"
    TRANSLATED_FILTER = "translated_filter"
    POST_FILTER = "post_filter"
    OUTPUT_ONLY = "output_only"
    UNSUPPORTED = "unsupported"
    BLOCKED_MISSING_MAPPING = "blocked_missing_mapping"


class Completeness(StrEnum):
    EXHAUSTIVE = "exhaustive"
    PAGINATED_EXHAUSTIVE = "paginated_exhaustive"
    BOUNDED = "bounded"
    SAMPLED = "sampled"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class ExecutionStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    EMPTY_VALID = "empty_valid"
    UNSUPPORTED = "unsupported"
    BLOCKED_MISSING_MAPPING = "blocked_missing_mapping"
    CONFIGURATION_ERROR = "configuration_error"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    PROVIDER_ERROR = "provider_error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    NORMALIZATION_ERROR = "normalization_error"
    SCHEMA_DRIFT = "schema_drift"
    CANCELLED = "cancelled"
    FAILED = "failed"


class GeographyRef(BaseModel):
    input: str
    name: str
    iso2: str | None = None
    iso3: str
    m49: str
    authority: str = "United Nations Statistics Division / M49"


class SearchIntent(BaseModel):
    schema_version: Literal[1] = 1
    keywords: str = ""
    location: str = ""
    date_from: str = ""
    date_to: str = ""
    geography: GeographyRef | None = None
    interpretation: str


class QueryPlanStep(BaseModel):
    source: str
    operation: str
    executable: bool
    parameters: dict[str, Any] = Field(default_factory=dict)
    native_parameters: dict[str, Any] = Field(default_factory=dict)
    criteria: dict[str, CapabilityMode] = Field(default_factory=dict)
    completeness: Completeness = Completeness.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class QueryPlan(BaseModel):
    schema_version: Literal[2] = 2
    contract_version: str = CONTRACT_VERSION
    intent: SearchIntent
    routes: list[QueryPlanStep]


class SourceExecution(BaseModel):
    source: str
    status: ExecutionStatus
    completeness: Completeness
    item_count: int = 0
    items: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None
    route: QueryPlanStep


def can_claim_empty_valid(*, completeness: Completeness, used_post_filter: bool) -> bool:
    """P0 invariant: a bounded/partial post-filter can never prove absence."""
    if not used_post_filter:
        return True
    return completeness in {Completeness.EXHAUSTIVE, Completeness.PAGINATED_EXHAUSTIVE}
