from __future__ import annotations

from ..base.api_factory import build_provider_router
from .descriptor import GDACS_DESCRIPTOR
from .service import GDACSService

router = build_provider_router(GDACS_DESCRIPTOR, GDACSService)
