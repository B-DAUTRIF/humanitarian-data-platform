# HDP 7.0.0 — semantic router implementation

## Architecture

V7 keeps the qualified modular-monolith boundary: FastAPI/Python is the reference semantic/acquisition engine, PostgreSQL/PostGIS persists structured metadata/provenance, raw and export artefacts remain file-backed, R is an optional analytical layer, and SPIP is publication/editorial only.

The semantic execution path is `user intent -> canonical HDP concepts -> provider capability -> verified provider translation -> native request -> provider response -> normalization -> provenance -> UI/export`.

## Contracts

The executable contracts are in `app/semantic_contracts.py`. The core P0 invariant is enforced by code and tests: a bounded/sampled/partial/unknown post-filter cannot produce `empty_valid`.

`query_fingerprint` identifies the normalized request and contract/mapping state. `result_snapshot_hash` identifies the result snapshot. They are intentionally different concepts.

## Provider status

- ReliefWeb: native structured country and date filters.
- World Bank: indicator discovery followed by native country/indicator observation requests using ISO3 and year range.
- UN SDG: M49 area resolution and native series/data requests.
- HDX HAPI: ISO3 is used as `location_code` where the HAPI contract documents that convention; endpoint-specific temporal semantics remain explicit.
- UNHCR: ISO3 with `cf_type=ISO`; generic geography is executed separately for origin and asylum and remains tagged by semantic role.
- HDX/CKAN: native free-text discovery; geography-only remains blocked until the exact HDX package-search geography contract is verified. Bounded post-filtering never proves absence.
- DHS: provider-specific country IDs are not guessed from ISO3; mapping remains blocked until the DHS country catalogue is resolved in the execution operation.
- UNICEF SDMX: dataflow-specific DSD/codelist key order is required before observation queries; generic geography is not fabricated.
- WHO GHO: the legacy catalogue remains available, while geographic observation routing is blocked pending requalification of the post-2025 World Health Data Hub contract.
- GDACS: event date filtering is native; geographic event filtering remains blocked until its exact Swagger request contract is represented.

## Qualification

Deterministic tests use mocks/fixtures and are separate from live provider monitoring. `tools/v7_semantic_live_acceptance.py` performs non-destructive live sentinels and reports configuration/provider failures separately from valid empty results.

A V7 release must not be promoted if the Rwanda regression can produce a false zero, a provider identifier is guessed, Query Plan differs from the native request, or deterministic/Windows qualification fails.
