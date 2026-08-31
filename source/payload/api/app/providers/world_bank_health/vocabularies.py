from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class WorldBankGeographyVocabulary:
    values: dict[str, dict[str, Any]]
    version_hash: str
    verified_at: str

    @classmethod
    def from_country_payload(cls, payload: Any) -> "WorldBankGeographyVocabulary":
        rows = payload[1] if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], list) else []
        values: dict[str, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict) or not row.get("id"): continue
            code = str(row["id"]).upper()
            region = row.get("region") if isinstance(row.get("region"), dict) else {}
            # World Bank country API identifies aggregates with region.id == NA.
            values[code] = {
                "id": code,
                "iso2Code": row.get("iso2Code"),
                "name": row.get("name"),
                "region_id": region.get("id"),
                "region_name": region.get("value"),
                "income_level": row.get("incomeLevel"),
                "lending_type": row.get("lendingType"),
                "capital_city": row.get("capitalCity"),
                "longitude": row.get("longitude"),
                "latitude": row.get("latitude"),
                "semantic_type": "aggregate" if region.get("id") == "NA" else "country_or_territory",
            }
        canonical = json.dumps(values, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        return cls(values, hashlib.sha256(canonical).hexdigest(), datetime.now(timezone.utc).isoformat())

    def semantic_type(self, code: str) -> str | None:
        item = self.values.get(code.strip().upper())
        return str(item["semantic_type"]) if item else None

    def to_record(self) -> dict[str, Any]:
        return {"provider":"world-bank-health","vocabulary":"country","version_hash":self.version_hash,"verified_at":self.verified_at,"count":len(self.values),"values":self.values}
