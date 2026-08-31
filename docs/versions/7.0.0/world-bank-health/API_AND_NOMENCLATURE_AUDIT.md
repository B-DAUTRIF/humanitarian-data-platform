# World Bank Health / Indicators API v2 — documentation and nomenclature audit

Status: evidence-backed implementation dossier for HDP V7.

## Official documentation corpus

Primary official World Bank Data Help Desk documentation reviewed for this connector:

1. About the Indicators API Documentation — V2 is the supported API version; API keys are not required for public Indicators API access.
2. API Basic Call Structures — URL and argument forms, date ranges, pagination, `per_page`, `mrv`, `mrnev`, `gapfill`, `frequency`, multiple indicators, footnotes, output/download formats, languages and delimiters.
3. Country API Queries — ISO 3166-1 alpha-3 and alpha-2 country identifiers, country name, World Bank region, income level, lending type, capital city, longitude and latitude.
4. Indicator API Queries — indicator code, name, unit, source ID, source note, source organization and topic mapping.
5. Topic API Queries — topic catalogue and topic-to-indicator discovery.
6. Aggregate API Queries — region, income and lending aggregates use provider aggregate codes in the country position. They are semantically distinct from sovereign countries.
7. Metadata API Queries — source, concept, metatype, metadata and keyword search operations.
8. New Features and Enhancements in V2 — metadata and downloadable list/table representations.
9. SDMX API Queries — additional standards-oriented access path and 15,000-data-point call limit for SDMX requests. This is documented as an annex provider interface, not silently substituted for the qualified Indicators JSON execution path.

Official evidence URLs are embedded in `source/payload/api/app/providers/world_bank_health/descriptor.py` and in the legacy source registry technical profile.

## Qualified HDP V7 connector scope

The V7 connector qualifies structured analytical acquisition through Indicators API v2 using JSON. It supports provider-native catalogue discovery, country metadata, topic/source catalogues, metadata keyword search, indicator metadata and observation acquisition. Other provider representations such as XML, JSONP, JSON-stat, ZIP CSV/XML/Excel downloads and SDMX are documented capabilities of the provider but are not claimed as qualified normalized execution paths in this implementation.

This distinction prevents the documentation of a World Bank feature from being mistaken for a tested HDP feature.

## Native parameters represented by the qualified execution contract

| Parameter / concept | Provider semantics | HDP V7 representation | UI type recommended | Qualification |
|---|---|---|---|---|
| `source` | World Bank source ID | integer, WDI default `2` | list/catalogue | qualified |
| country | country path segment | verified sovereign ISO3; multi-value `;` | geography multiselect | qualified |
| indicator | series code path segment | one or more codes separated by `;` | searchable multi-select | qualified |
| `date` | year or provider-supported period/range | text/range generated from canonical time | date/period control | qualified for annual semantic routing |
| `page` | result page | positive integer | numeric | qualified |
| `per_page` | results per page | positive integer | numeric | qualified |
| `mrv` | most recent values | optional integer | numeric | qualified request construction |
| `mrnev` | most recent non-empty values | optional integer | numeric | qualified request construction |
| `gapfill` | back-fill with MRV | boolean -> `Y` | checkbox | qualified request construction |
| `frequency` | Y/Q/M with MRV | enum | list | qualified request construction |
| `footnote` | return footnote detail | boolean -> `y` | checkbox | qualified request construction |
| `format` | provider output representation | fixed `json` for normalized V7 path | read-only qualified format | qualified |
| language | language URL prefix | string | list | qualified for implemented prefix path |
| metadata search query | metadata keyword search | text path segment | search text | qualified request construction/live gate |

Provider documentation also specifies JSONP (`prefix`), JSON-stat, download formats (`downloadformat`), downloadable table/list formatting (`dataformat`), additional local languages and high-frequency/YTD date forms. These are retained in the documentary inventory but are not promoted to `IMPLÉMENTÉ ET QUALIFIÉ` until dedicated HDP handling and tests exist.

## Nomenclatures and crosswalk requirements

### Countries

The Country API exposes ISO 3166-1 alpha-3 and alpha-2 codes. HDP semantic routing uses verified sovereign ISO3 where a country is intended. A three-character token is **not sufficient evidence** of sovereign-country semantics.

### World Bank aggregate identifiers

The World Bank API permits region, income and lending-group aggregate codes in the same path position used by countries. The first implementation audit exposed exactly this ambiguity with `SSA`. The connector now explicitly prevents common aggregate identifiers from passing through the sovereign-country route. The provider catalogue remains the authoritative dynamic source; the static guard is a safety barrier, not a claim of exhaustive nomenclature authority.

Aggregate queries must therefore carry an explicit HDP semantic type such as `world_bank_aggregate`, never masquerade as ISO3 geography.

### Regions, income groups and lending types

Country metadata includes World Bank-specific region, income-level and lending-type identifiers. These should be cached as provider vocabularies and crosswalked only when an external equivalence is verified. HDP must not infer an ISO/M49 equivalence from labels alone.

### Indicator codes

Indicator codes are provider series identifiers. Health discovery is anchored on WDI source `2` by default, but the source ID is preserved in provenance. Indicator name, unit, source note, source organization and topics are retained as discovery/metadata evidence.

### Topics

World Bank topics are provider-native high-level classifications. They are useful for discovery but are not equivalent to ICD, WHO GHO, SDG or HDP internal health taxonomies without an explicit mapping table and evidence.

## Annex data interfaces

- Metadata API: useful for semantic enrichment, source concepts and metadata search.
- SDMX API: useful for standards-oriented bulk/structured workflows; separate contract and limits apply.
- Data Catalog API: distinct World Bank API family and not treated as an implicit substitute for Indicators API.
- Download formats: provider offers ZIP CSV/XML/Excel on supported calls; these require a separate download/provenance path before qualification in HDP.

## Safety / false-zero rules

- HTTP failures, parse failures, provider error payloads and mapping failures are errors, not empty results.
- A bounded catalogue search cannot prove that an indicator does not exist outside the bound.
- A syntactically valid three-letter World Bank identifier does not prove sovereign-country semantics.
- No aggregate identifier is silently transformed into or accepted as ISO3.
- The normalized result preserves the native observation under `_native` and records the native request URL in provenance.

## Provider constraints retained from official documentation

The official Basic Call Structures documentation notes limits including a maximum of 60 indicators in a multi-indicator request, path/URL length limits, and provider-specific interactions such as frequency with MRV. These constraints are documentary evidence. The current qualified V7 builder validates the core route and parameter types but does not yet claim client-side enforcement of every provider URL-length/download-format rule.
