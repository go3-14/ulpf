# ULPF — Universal Log Pre-processing Framework

### Consolidated Build Specification — v3 (SIH 2026, Problem Statement 26156)

ULPF is a high-performance, long-running microservice designed to ingest logs from perimeter network devices (firewalls, routers, VPN gateways) across **four major log formats**: **Syslog (RFC3164/RFC5424)**, **CEF (Common Event Format)**, **LEEF (Log Event Extended Format)**, and **JSON**.

ULPF parses and normalizes logs into the **OCSF (Open Cybersecurity Schema Framework)** schema, **Network Activity** class (`category_uid: 4`, `class_uid: 4001`), while preserving full raw log losslessness, traceability, and zero-code plug-and-play onboarding.

---

## 🌟 Key Features

1. **Multi-Format Ingestion**: Supports Syslog, CEF, LEEF, and JSON out of the box.
2. **OCSF 4001 Normalization**: Strict type-safe normalization to OCSF `Network Activity` (class 4001).
3. **100% Lossless Preservation**: Raw bytes stored verbatim (with base64 fallback for binary/non-UTF8 data). Unmapped attributes are automatically preserved inside OCSF's native `unmapped` object.
4. **Plug-and-Play Onboarding**: Onboard a new device source by adding **one YAML file** — **zero Python code changes required**.
5. **Dual-Store Traceability**: Shared event ID (`metadata.uid`) links normalized records directly to raw log byte offsets for $O(1)$ retrieval.
6. **Air-Gapped & Containerized**: Zero outbound network access at runtime. Schema dependencies resolved from local disk.

---

## 🚀 Quick Start

### 1. Installation

Python 3.11+ is required.

```bash
# Clone the repository
git clone https://github.com/your-org/ulpf.git
cd ulpf

# Install runtime dependencies
pip install -r requirements.txt

# Install dev/test dependencies (optional)
pip install -r requirements-dev.txt
```

### 2. Running Unit & Integration Tests

```bash
python -m pytest
```

---

## 💻 CLI Usage (`ulpf`)

```bash
# 1. Start long-running service (Spool Watcher + UDP Listener + REST API)
python -m cli.main serve

# 2. Process a log file directly via CLI
python -m cli.main process samples/cisco_asa_syslog.log

# 3. Lookup raw and normalized event side-by-side by Event ID
python -m cli.main lookup <event_uuid>

# 4. Search normalized events
python -m cli.main search --source cisco_asa --limit 10

# 5. Check real-time metrics
python -m cli.main status

# 6. Hot-reload YAML mappings without restarting service
python -m cli.main reload
```

To rebuild an existing normalized store after a schema or mapping upgrade (raw
files and event IDs are preserved), run:

```bash
python scripts/rebuild_normalized_store.py --storage-dir ./storage_data
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Returns service status and count of active mapping configs |
| `/events` | GET | Search normalized OCSF events (`source`, `format`, `src_ip`, `dst_ip`, `dst_port`, `since`, `until`, `limit`) |
| `/events/{id}` | GET | Fetch normalized OCSF event by UUID |
| `/events/{id}/raw` | GET | Fetch original raw log bytes verbatim by UUID |
| `/ingest` | POST | Ingest raw log line(s) via HTTP payload |
| `/metrics` | GET | Service throughput and latency statistics |
| `/mappings/reload` | POST | Hot-reload YAML mapping configurations |

---

## 🧩 Adding a New Log Source in 5 Minutes (Zero-Code Onboarding)

To add support for a new log source (e.g. FortiGate Firewall over Syslog):

1. Create a new YAML file in `mappings/fortigate_syslog.yaml`:

```yaml
source: fortigate_syslog
format: syslog
description: "FortiGate Firewall via Syslog"

ocsf:
  version: "1.9.0"
  class_uid: 4001
  category_uid: 4

priority: 100
match:
  all:
    - field: message
      contains: "devname=FG100D"

constants:
  metadata.product.vendor_name: "Fortinet"
  metadata.product.name: "FortiGate"

field_map:
  src:     { to: src_endpoint.ip,               type: ip }
  spt:     { to: src_endpoint.port,             type: port }
  dst:     { to: dst_endpoint.ip,               type: ip }
  dpt:     { to: dst_endpoint.port,             type: port }
  proto:   { to: connection_info.protocol_name, type: str }

defaults:
  activity_id: 6
  severity_id: 1
```

2. Trigger mapping reload via CLI or API:
```bash
python -m cli.main reload
# or curl -X POST http://localhost:8000/mappings/reload
```

3. Any incoming log matching `devname=FG100D` will now automatically route and normalize under `fortigate_syslog` with **zero code modifications**.

---

## 🐳 Docker & Air-Gap Verification

### Build Container

```bash
docker build -t ulpf .
```

### Run A — Air-Gap Verification (Requirement j)
Runs with `--network none` to prove zero outbound network dependencies:
```bash
docker run --rm --network none \
  -v "$PWD/storage_data:/app/storage_data" \
  -v "$PWD/samples:/app/samples:ro" \
  ulpf python -m cli.main process /app/samples/paloalto_cef.log
```

### Run B — API & Listener Container
```bash
docker run --rm -p 8000:8000 -p 5514:5514/udp \
  -v "$PWD/storage_data:/app/storage_data" \
  -v "$PWD/spool:/app/spool" \
  ulpf
```

### Zero-Outbound Network Call Proof
To verify no outbound HTTP requests exist in application code:
```bash
grep -rn "requests\|urllib\|http://\|https://" --include="*.py" .
```
*(Only hits in `scripts/fetch_ocsf_schema.py` which is dev-time only, and Docker healthcheck).*

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ULPF_STORAGE_DIR` | `./storage_data` | Root directory for partitioned NDJSON storage |
| `ULPF_SPOOL_DIR` | `./spool` | Directory polled by spool watcher |
| `ULPF_API_PORT` | `8000` | REST API port |
| `ULPF_UDP_PORT` | `5514` | UDP Syslog listener port |
| `ULPF_POLL_INTERVAL` | `1.0` | Spool watcher polling interval in seconds |
| `ULPF_LOG_LEVEL` | `INFO` | Logging verbosity |

---

## 📁 Storage Architecture

Data is written to date and source partitioned NDJSON flat files:

```
storage_data/
  raw/         dt=YYYY-MM-DD/source=<source_id>/raw-0001.ndjson
  normalized/  dt=YYYY-MM-DD/source=<source_id>/events-0001.ndjson
  failed/      dt=YYYY-MM-DD/source=failed/failed-0001.ndjson
  index/       raw_index.ndjson
```

---

## 💡 Benchmark

Run throughput benchmark:
```bash
python scripts/benchmark.py
```
*Result*: ~250+ events/sec single-process Python execution with full OCSF validation and disk persistence.
