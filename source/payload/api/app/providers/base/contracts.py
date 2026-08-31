from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ConfigVisibility(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SECRET = "secret"


@dataclass(frozen=True)
class ProviderConfigField:
    name: str
    type: str
    visibility: ConfigVisibility = ConfigVisibility.PUBLIC
    required: bool = False
    default: Any = None
    project_override: bool = True
    execution_override: bool = False
    description: str = ""


@dataclass(frozen=True)
class ProviderCapability:
    name: str
    mode: str
    evidence: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class ProviderOperationDescriptor:
    name: str
    content_type: str
    methods: tuple[str, ...]
    collection: bool = True
    item: bool = False


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    name: str
    api_version: str
    base_url: str
    operations: tuple[ProviderOperationDescriptor, ...]
    capabilities: tuple[ProviderCapability, ...]
    configuration: tuple[ProviderConfigField, ...]
    content_types: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    runtime_limits: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_provider_configuration(
    descriptor: ProviderDescriptor,
    *,
    global_settings: dict[str, Any] | None = None,
    project_settings: dict[str, Any] | None = None,
    execution_overrides: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Resolve defaults -> global -> project -> authorized execution override.

    Returns both value and origin so provenance/UI can explain effective config.
    Secret fields remain values internally; callers are responsible for visibility.
    """
    global_settings = global_settings or {}
    project_settings = project_settings or {}
    execution_overrides = execution_overrides or {}
    result: dict[str, dict[str, Any]] = {}
    for spec in descriptor.configuration:
        value, origin = spec.default, "default"
        if global_settings.get(spec.name) not in (None, ""):
            value, origin = global_settings[spec.name], "global"
        if spec.project_override and project_settings.get(spec.name) not in (None, ""):
            value, origin = project_settings[spec.name], "project"
        if spec.execution_override and execution_overrides.get(spec.name) not in (None, ""):
            value, origin = execution_overrides[spec.name], "execution"
        if spec.required and value in (None, ""):
            raise ValueError(f"Missing required provider configuration: {spec.name}")
        result[spec.name] = {"value": value, "origin": origin, "visibility": spec.visibility.value}
    return result
