# Improved execution protocol — HDP V7 World Bank Health

This file persists the operationalized version of the user request.

## Mission

Implement and qualify the World Bank Health connector in HDP V7 using the same evidence-first provider architecture principles established for ReliefWeb and HDX.

## Required phases

1. **Documentary evidence collection**: official API documentation, endpoint specifications, parameters, provider constraints, error semantics, nomenclatures, metadata services, standards/annex interfaces and licensing/usage references.
2. **Provider capability inventory**: distinguish documented provider capability, implemented HDP capability, qualified capability, blocked/deferred capability and out-of-scope annex capability.
3. **Architecture**: provider descriptor + provider service + semantic integration compatibility + native provenance + normalization + explicit nomenclature handling + anti-false-zero behavior.
4. **Parameter/UI model**: identify native parameters, type/cardinality/constraints and recommended HDP control; do not claim UI exposure until the legacy/project schema actually exposes it.
5. **Testing**: for every declared connector functionality, execute 10 deterministic debug/implementation/audit cycles. A non-executed cycle is never PASS.
6. **Live qualification**: separately execute non-destructive real-provider checks for country metadata, indicator metadata, ancillary catalogues/metadata and health observations. Provider/network/configuration errors remain explicit failures and never become empty data.
7. **Regression**: run the existing HDP V7 semantic suite and legacy V6 quality gate; no connector implementation may make the qualified baseline regress.
8. **Windows/build**: require the existing Windows build/validation workflows to remain green for the candidate commit before describing HDP V7 integration as build-compatible.
9. **Traceability**: persist source files, tests, reports, CI run IDs, discovered defects, fixes and residual debt in GitHub.
10. **Business evaluation**: assess usefulness for humanitarian/public-health work, not merely HTTP/API correctness.

## Acceptance criteria

- official evidence is cited in the provider contract/documentation;
- sovereign countries and World Bank aggregate identifiers are not conflated;
- native request parameters and URLs are recoverable for provenance;
- structured JSON observations normalize without discarding the native row;
- 10 deterministic cycles pass for every declared connector functionality;
- live provider gate passes, or the exact provider-side blocker is recorded;
- V7 regression gate remains green;
- Windows build/validation remains green;
- detailed GitHub implementation log and final report exist;
- known gaps are explicit and are not re-labelled as implemented.

## Promotion rule

This connector work may qualify the World Bank component and a V7 user-test candidate, but it does not by itself authorize promotion of `main` or a stable V7 release. Repository release policy and all remaining provider gates still apply.
