from __future__ import annotations

"""HDP V7 explicit runtime alias.

The historical ``main_v6`` module remains the compatibility entrypoint used by
qualified packaging tools; it now boots the V7 semantic schema and API.
"""

from .main_v6 import app

app.version = "7.0.0"
app.title = "Humanitarian Data Platform"
