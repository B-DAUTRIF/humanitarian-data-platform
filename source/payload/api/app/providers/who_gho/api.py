from __future__ import annotations

from ..base.api_factory import build_provider_router
from .descriptor import WHO_GHO_DESCRIPTOR
from .service import WHOGHOService

router = build_provider_router(WHO_GHO_DESCRIPTOR, WHOGHOService)
