from __future__ import annotations

from ..base.api_factory import build_provider_router
from .descriptor import UN_SDG_DESCRIPTOR
from .service import UNSDGService

router = build_provider_router(UN_SDG_DESCRIPTOR, UNSDGService)
