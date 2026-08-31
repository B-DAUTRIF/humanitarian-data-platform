# HDP V7 — World Bank Health connector implementation log

## Scope

Connector: World Bank Indicators API v2, with health-oriented discovery anchored on World Development Indicators (source 2), integrated into the HDP V7 semantic architecture.

Base commit: `1b41b96eb4ae6d789d9b4166eb21e6a7aa8f2da1`.
Working branch: `feat/v7-world-bank-health-implementation`.

## Procedure

1. Collect and verify official documentation, API contracts, nomenclatures and ancillary catalogues.
2. Derive connector architecture from the qualified ReliefWeb/HDX patterns while preserving provider-native semantics.
3. Build a functionality inventory and deterministic test matrix.
4. Execute 10 debug/implementation/audit cycles per declared connector functionality.
5. Execute non-destructive live acceptance separately from deterministic qualification.
6. Integrate into HDP V7 semantic routing, provenance, clients and qualification workflow.
7. Produce final technical and business-oriented evaluation.

## Anti-hallucination rule

A test not executed is never marked PASS. Provider failures, mapping failures, bounded results and configuration failures must never be interpreted as valid empty data.

## Documentation collected

Official World Bank Data Help Desk / Indicators API v2 material reviewed:

- Developer Information overview — distinguishes Indicators API, Data Catalog API and Projects API.
- About the Indicators API Documentation — V2 is current; V1 is retired; public Indicators API requires no API key.
- API Basic Call Structures — URL-based and argument-based calls; date/date ranges; pagination; MRV/MRNEV; gap-fill; frequency; multi-indicator queries; footnotes; response formats and delimiters.
- Country API Queries — ISO 3166-1 alpha-3 and alpha-2 codes, World Bank region, income level, lending type, capital city and coordinates.
- Indicator API Queries — indicator code/name/unit/source/source note/source organization/topics; source disambiguation.
- Topic API Queries — topic catalogue and indicator filtering by topic.
- Metadata API Queries — sources, concepts, metadata concepts and metatypes.
- Aggregate API Queries — region, income-level and lending aggregates use codes in the country position and must not be conflated with sovereign countries.

## Provider nomenclatures identified

- ISO 3166-1 alpha-3 / alpha-2 country codes returned by the Country API.
- World Bank country/aggregate identifiers.
- World Bank Region codes.
- World Bank Income Level codes.
- World Bank Lending Type codes.
- World Bank Topic IDs.
- World Bank Source IDs, notably source `2` = World Development Indicators.
- Indicator codes (series IDs).
- Temporal periods: annual and, for supporting series, monthly/quarterly frequencies.

## Initial architecture decisions

- Keep `world-bank-health` as a provider-specific HDP connector.
- Separate indicator catalogue discovery from observation acquisition.
- Preserve native country/indicator/date requests in provenance.
- Resolve canonical geography to ISO3 only when evidence supports a sovereign-country mapping; preserve aggregates as a distinct semantic type.
- Never guess a World Bank aggregate code from ISO3 or vice versa.
- Preserve `source=2` for the WDI health profile unless the user explicitly selects another verified source.
- Expose provider-native optional parameters rather than hiding them behind a generic search abstraction.
- Treat provider/network errors as errors, never as `empty_valid`.

## Work status

Started. Final status will be appended after implementation and executed qualification.
