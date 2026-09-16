# ULPF Architecture

Pipeline:

```text
ingest (spool | UDP | HTTP)
  -> detect
  -> parse
  -> identify source from YAML
  -> normalize to OCSF Network Activity shape
  -> validate
  -> store raw and normalized
  -> API/CLI
```

## Why OCSF

OCSF is vendor-neutral and security-native, so Cisco ASA, Palo Alto CEF, LEEF devices, and JSON devices can land in one event shape. ULPF does not mix OCSF with ECS and does not add custom top-level fields. Fields without a defined target go into OCSF's `unmapped` object.

## Plug-and-Play Onboarding

Source identification is YAML-driven, not hardcoded:

```yaml
match:
  all:
    - field: tag
      regex: "^%ASA-"
```

Only configs whose `format` matches the detected parser format are considered, and the highest-priority matching config wins. That is the key zero-code property: a second syslog device can be added with one YAML file.

## Losslessness and Traceability

ULPF stores raw bytes first. UTF-8 logs are stored as text; non-UTF-8 bytes are base64 encoded and decoded back in `read_raw()`. The normalized event uses the same event ID in `metadata.uid`, so the raw-normalized link survives export.

The normalized side also keeps every parsed-but-unmapped field in `unmapped`, and transform failures are recorded under `_ulpf_transform_errors`.

## Air-Gap Position

Runtime code never fetches schemas, GeoIP data, or cloud services. The UDP listener is an inbound socket bind on port 5514; it is not an outbound connection.

## Adapted vs. Built Here

Adapted standards: OCSF, Syslog, CEF, LEEF, JSON, and the ingest-normalize-store pattern.

Built here: the YAML-driven source identification, config-driven mapping and type coercion engine, dual raw/normalized storage model, traceable lookup API/CLI, and tests that prove config-only onboarding.

## Production Path

This prototype writes partitioned NDJSON for demo and data-lake landing. A production deployment would put a partitioned queue in front of stateless ULPF workers, then sink normalized events to Elasticsearch/OpenSearch or object storage queried by Athena/Spark. Horizontal scaling is per event because normalization has no cross-event state.

## Validation Note

This build ships a trimmed local OCSF Network Activity schema subset to keep the runtime air-gapped and the project runnable. Before final competition submission, replace `scripts/fetch_ocsf_schema.py` with an official OCSF schema crawler and commit the downloaded schema bundle.
