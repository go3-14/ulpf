# Requirements traceability

| Requirement | Implementation | Proof |
|---|---|---|
| a | `ingest/pipeline.py`, raw/index stores | `pytest -q` lossless/fallback tests |
| b | `parsers/` and mapping fixtures | parser and mapping tests |
| c | `schema/validate.py` and bundled classes | class validation tests |
| d | deterministic IDs, raw API, provenance | dedup/provenance tests |
| e | YAML mappings and onboarding | mapping golden tests |
| f | search and correlation | search/correlation tests |
| g | `exports/` | exporter tests |
| h | coverage metrics | coverage tests |
| i | onboarding CLI | onboarding tests |
| j | air-gap scripts | static network test |
| k | Dockerfile and test stage | Docker contract test |
