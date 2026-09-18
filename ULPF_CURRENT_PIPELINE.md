# ULPF: Current Pipeline and Implemented Capabilities

This document describes the system as it exists today. It is a local, air-gap-capable prototype for normalizing network-security logs into OCSF 1.9.0 Network Activity events.

```text
CLI file / Spool .log files / UDP syslog / HTTP POST
                         |
                         v
                Format detection
                         |
                         v
            Format-specific parser
                         |
                         v
        YAML source matching + mapping
                         |
                         v
       OCSF 1.9.0 normalization + validation
                         |
                         v
 Raw store --> raw index --> normalized store
                         |
                         v
     REST lookup/search, CLI lookup/search, metrics
```

## 1. Input paths

ULPF accepts Syslog, CEF, LEEF, and JSON records.

- **CLI:** `python -m cli.main process <file>` reads a file and processes each nonblank line. A complete JSON document is processed as one event.
- **Spool watcher:** `python -m cli.main serve` polls `*.log` files in `ULPF_SPOOL_DIR` (default: `./spool`). It tracks offsets, waits for newline-terminated records, processes complete records, and moves completed files to `.processed`.
- **UDP Syslog:** the service listens on UDP port `5514` by default and processes received datagrams.
- **HTTP:** `POST /ingest` accepts JSON in the form `{"logs": "..."}` or `{"logs": ["...", "..."]}`.

Paths, ports, logging, and the spool polling interval are configured in `config.py` through `ULPF_*` environment variables.

## 2. Detection and parsing

`ingest/pipeline.py` decodes an incoming record for format detection and dispatches it to a parser.

| Format | Implemented extraction |
|---|---|
| Syslog | PRI, facility/severity, timestamp, hostname, tag, message, key-value fields, and Cisco ASA connection/deny patterns |
| CEF | Optional Syslog envelope, CEF header fields, escaped delimiters, and extension key-values |
| LEEF | Optional Syslog envelope, LEEF 1.0/2.0 headers, including custom delimiters |
| JSON | Nested objects flattened to dotted keys; scalar arrays joined as comma-separated values |

Unrecognized or unparsable input is written to the failed-event store.

## 3. Source matching and onboarding

Mappings in `mappings/*.yaml` identify sources and define normalization without source-specific Python code.

Each mapping can specify:

- input format and match conditions
- priority, vendor, and product constants
- source-field to OCSF-field mappings
- transformations (`str`, `int`, `float`, `bool`, `ip`, `port`, and `enum`)
- defaults and timestamp configuration

The current mapping set covers Cisco ASA, FortiGate, generic JSON, generic LEEF, generic Syslog, Palo Alto CEF, and XYPRO CEF. A new device using an already-supported format normally requires one YAML mapping and a reload, not a Python change.

## 4. Normalization and validation

For a successfully parsed and matched event, ULPF:

1. Generates a UUID event ID.
2. Builds an OCSF Network Activity event.
3. Applies mapping constants, defaults, field maps, and conversions.
4. Computes `type_uid` from class and activity IDs.
5. Preserves parsed-but-unmapped attributes under `unmapped`.
6. Adds labels for `ulpf`, source ID, and detected format.
7. Validates the result with the bundled, offline OCSF 1.9.0 schema.

The normalized event uses the UUID in `metadata.uid`, linking it to the original event.

## 5. Storage and traceability

Successful processing writes data in this order:

1. Store the original raw bytes.
2. Add an event-ID-to-file-offset index entry.
3. Store the normalized OCSF event.

Storage is date- and source-partitioned NDJSON:

```text
storage_data/
  raw/dt=YYYY-MM-DD/source=<source>/raw-0001.ndjson
  normalized/dt=YYYY-MM-DD/source=<source>/events-0001.ndjson
  failed/dt=YYYY-MM-DD/source=failed/failed-0001.ndjson
  index/raw_index.ndjson
```

UTF-8 raw records are stored as text. Non-UTF-8 records are Base64 encoded to preserve their bytes. Partition files rotate at 64 MB; writes use per-file locks, flush after each record, and fsync during clean shutdown.

## 6. Outputs and operations

### REST API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Service status and loaded mapping count |
| `GET /events` | Search normalized events across sources and formats |
| `GET /events/{id}` | Retrieve one normalized OCSF event |
| `GET /events/{id}/raw` | Retrieve its original raw record |
| `POST /ingest` | Ingest one or more text log records |
| `GET /metrics` | Process/failure counts and latency statistics |
| `POST /mappings/reload` | Reload YAML mappings |

### CLI

The CLI supplies `serve`, `process`, `lookup`, `search`, `status`, and `reload` commands.

## 7. Container and air-gap behavior

The Docker image runs as a non-root user, exposes REST and UDP ports, and mounts storage and spool volumes. The OCSF schema is bundled locally. Runtime processing makes no outbound network calls, so the documented air-gap mode runs with `--network none`.

## 8. Current prototype boundaries

ULPF is intentionally a single-node prototype rather than a production distributed data platform.

- Built-in formats are Syslog, CEF, LEEF, and JSON; XML, CSV, cloud-specific, and proprietary formats are not yet implemented.
- Data is stored in local NDJSON files; there is no Kafka/RabbitMQ ingress, object-store sink, Elasticsearch/OpenSearch integration, or distributed query engine.
- Ingestion is single-process and metrics/index caching is in-memory.
- Authentication, TLS termination, RBAC, tenant isolation, and outbound SIEM connectors are not implemented.
- The production direction is documented as queue-backed, horizontally scalable workers with a dedicated search/SIEM or data-lake sink.
