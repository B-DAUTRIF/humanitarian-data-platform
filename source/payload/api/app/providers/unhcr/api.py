from __future__ import annotations

from ..base.api_factory import build_provider_router
from .descriptor import UNHCR_DESCRIPTOR
from .service import UNHCRService

router = build_provider_router(UNHCR_DESCRIPTOR, UNHCRService)
