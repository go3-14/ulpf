# ULPF Architecture Document

## 1. System Architecture & Ingestion Pipeline Flow

```
+-------------------------------------------------------------------------------+
|                             INGRESS SOURCES                                   |
|   Spool Directory (*.log)   |   UDP Listener (5514)   |   HTTP POST /ingest     |
+-------------------------------------------------------------------------------+
                                      |
                                      v
                             ingest/pipeline.py
                                      |
       +------------------------------+------------------------------+
       |                              |                              |
       v                              v                              v
parsers/detect.py            parsers/*.py                    mappings/matcher.py
(Format Detection)          (Syslog/CEF/LEEF/JSON)          (Config-Driven Match)
       |                              |                              |
       +------------------------------+------------------------------+
                                      |
                                      v
                             schema/normalize.py
                           (Generic OCSF Engine)
                                      |
                                      v
                             schema/validate.py
                         (Local $ref JSON Schema)
                                      |
            +-------------------------+-------------------------+
            |                                                   |
            v                                                   v
  storage/raw_store.py                                storage/normalized_store.py
 (Raw Bytes + Base64)                                (OCSF 4001 Partitioned NDJSON)
            |                                                   |
            +-------------------------+-------------------------+
                                      |
                                      v
                             storage/index.py
                     (Shared Event ID: metadata.uid)
```

---

## 2. Why OCSF (Open Cybersecurity Schema Framework)?

ULPF standardizes exclusively on **OCSF Class 4001 (Network Activity)** under Category 4 (Network).

- **Vendor Neutrality**: Eliminates proprietary log silos across Cisco, Palo Alto, Fortinet, and generic devices.
- **Security-Native Taxonomy**: Provides strongly-typed enums (`activity_id`, `severity_id`), IP representations, and integer ports essential for automated SIEM analytics and machine learning.
- **Native Losslessness (`unmapped`)**: Unlike schemas that drop unrecognized fields or force arbitrary top-level pollution, OCSF defines a standard top-level `unmapped` dictionary. Any parsed attribute not mapped into the schema is retained verbatim in `unmapped`.

---

## 3. Plug-and-Play Onboarding Mechanism (Zero-Code)

Zero-code onboarding is achieved by decoupling parsing, source matching, and normalization into configuration:

1. **Format Parsers** extract source-specific attributes into a flat key-value dictionary.
2. **`mappings/matcher.py`** evaluates matching criteria defined in YAML (`match.all` conditions such as tag regex or string equality) against the parsed dictionary.
3. **`schema/normalize.py`** executes generic field transformations (`ip`, `port`, `enum`, `epoch_ms`) based on the YAML `field_map`.

Because source identification and field mapping are defined entirely in YAML, **no `.py` files are ever modified when adding or updating log sources**.

---

## 4. Traceability & Losslessness

- **Traceability**: Every ingested log is assigned a UUID (`metadata.uid`). This UUID is stamped on the OCSF event and recorded in `storage/index.py` alongside the exact file path, byte offset, and length of the corresponding raw record. `GET /events/{id}` and `GET /events/{id}/raw` query this index for instant $O(1)$ dual-store retrieval.
- **Losslessness**:
  - Raw log bytes are stored verbatim. If non-UTF8 bytes are encountered, ULPF falls back to base64 encoding without dropping data.
  - Normalized records retain all unconsumed parsed fields in `unmapped`, guaranteeing no attribute is discarded.

---

## 5. Adapted vs. Built Here (Honest Technical Scope)

### Standard / External Specifications Adapted
- **OCSF 1.9.0 Specification**: Standard cybersecurity taxonomy (Class 4001), bundled locally for offline validation.
- **Format Standards**: RFC3164/RFC5424 Syslog, ArcSight CEF, QRadar LEEF 1.0/2.0 specs.

### Built Custom in ULPF
- **Config-Driven Matcher & Engine**: Zero-vendor-logic generic engine in `schema/normalize.py`.
- **Local Off-Line Schema Validator**: Disk-based `$ref` schema resolution using `jsonschema` + `referencing`.
- **Thread-Safe Partitioned NDJSON Writer**: Custom lock-per-partition storage engine supporting concurrent thread writes.
- **Spool Polling Watcher**: Partial-write safe directory watcher with offset persistence.

---

## 6. Production Scale Path

1. **Ingestion Layer**: Deploy Kafka or RabbitMQ as the ingress queue in front of ULPF.
2. **Stateless Processing**: Scale ULPF containers horizontally behind consumer groups. Because normalization is stateless per line, throughput scales linearly.
3. **Storage Sink**: Direct the Partitioned NDJSON Landing Zone to S3 / Data Lake or stream directly into Elasticsearch / OpenSearch / SIEM platforms.
