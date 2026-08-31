from __future__ import annotations

"""Versioned contracts shared by the four HDP bounded contexts."""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

CONTRACT_VERSION = "7.0.0"


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
    iso3: str
    m49: str
    authority: str = "United Nations Statistics Division / M49"


class SearchIntent(BaseModel):
    schema_version: Literal[1] = 1
    keywords: str = ""
    canonical_keywords: str = ""
    location: str = ""
    date_from: str = ""
    date_to: str = ""
    geography: GeographyRef | None = None
    interpretation: str
    semantic_notes: list[str] = Field(default_factory=list)


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
    query_fingerprint: str


class SourceExecution(BaseModel):
    source: str
    status: ExecutionStatus
    completeness: Completeness
    item_count: int = 0
    items: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None
    native_request: dict[str, Any] = Field(default_factory=dict)
    response_hash: str | None = None
    route: QueryPlanStep


class ProvenanceRecord(BaseModel):
    query_fingerprint: str
    result_snapshot_hash: str
    contract_version: str = CONTRACT_VERSION
    source_executions: list[dict[str, Any]] = Field(default_factory=list)


def can_claim_empty_valid(*, completeness: Completeness, used_post_filter: bool) -> bool:
    """Return True only when the provider coverage can actually prove absence.

    A bounded, sampled, partial or unknown acquisition can never establish a true
    zero, even when all filtering was native. Post-filtering does not weaken an
    exhaustive/paginated-exhaustive acquisition when the whole acquired result set
    is filtered locally, but every non-exhaustive state remains non-conclusive.
    """
    del used_post_filter  # retained in the public contract for backwards compatibility
    return completeness in {Completeness.EXHAUSTIVE, Completeness.PAGINATED_EXHAUSTIVE}
