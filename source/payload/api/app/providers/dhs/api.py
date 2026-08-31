from __future__ import annotations

from ..base.api_factory import build_provider_router
from .descriptor import DHS_DESCRIPTOR
from .service import DHSService

router = build_provider_router(DHS_DESCRIPTOR, DHSService)
