from __future__ import annotations

from ..base.api_factory import build_provider_router
from .descriptor import UNICEF_SDMX_DESCRIPTOR
from .service import UNICEFSDMXService

router = build_provider_router(UNICEF_SDMX_DESCRIPTOR, UNICEFSDMXService)
