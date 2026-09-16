# ULPF - Universal Log Pre-processing Framework

ULPF ingests perimeter-device logs in Syslog, CEF, LEEF, and JSON, parses them into source fields, normalizes them into an OCSF Network Activity-shaped event, and stores both the normalized event and byte-identical raw log linked by `metadata.uid`.

## Status

This implementation covers the SIH core path:

- Four parsers: Syslog, CEF, LEEF, JSON
- YAML-driven source identification and field mapping
- Lossless raw storage with base64 fallback
- Partitioned NDJSON raw, normalized, and failed storage
- FastAPI API and argparse CLI
- Spool watcher, UDP syslog listener, metrics, Docker packaging
- Tests for parsing, normalization, API, losslessness, onboarding, and writer concurrency

OCSF validation currently uses a documented trimmed local schema subset. The dev-time `scripts/fetch_ocsf_schema.py` is a placeholder and must be replaced with an official schema crawler before claiming full official OCSF validation.

## Install

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m pip install -r requirements-dev.txt
```

Runtime dependencies are only:

```text
pyyaml
fastapi
uvicorn
jsonschema
referencing
```

## Test

```powershell
py -3 -m pytest -q
```

Current result on this machine: `15 passed`.

## Run

Process a file:

```powershell
py -3 -m cli.main process samples/paloalto_cef.log
```

Start the long-running service:

```powershell
py -3 -m cli.main serve
```

Useful endpoints:

```text
GET  /health
POST /ingest
GET  /events/{event_id}
GET  /events/{event_id}/raw
GET  /events?dst_port=443
GET  /metrics
POST /mappings/reload
```

Lookup from CLI:

```powershell
py -3 -m cli.main lookup <event_id>
```

Search from CLI:

```powershell
py -3 -m cli.main search --format cef --dst-port 443
```

## Environment Variables

```text
ULPF_STORAGE_DIR=storage_data
ULPF_SPOOL_DIR=spool
ULPF_API_HOST=0.0.0.0
ULPF_API_PORT=8000
ULPF_UDP_HOST=0.0.0.0
ULPF_UDP_PORT=5514
ULPF_LOG_LEVEL=INFO
```

## Storage Layout

```text
storage_data/
  raw/dt=YYYY-MM-DD/source=<source>/raw-0001.ndjson
  normalized/dt=YYYY-MM-DD/source=<source>/events-0001.ndjson
  failed/dt=YYYY-MM-DD/failed-0001.ndjson
  index/raw_index.ndjson
  index/normalized_index.ndjson
```

Raw is written before normalized. An orphaned raw record is recoverable; an orphaned normalized record would not preserve the original evidence.

## Adding a New Log Source in 5 Minutes

Add one YAML file under `mappings/`:

```yaml
source: fortigate_syslog
format: syslog
ocsf: { version: "subset-1", class_uid: 4001, category_uid: 4 }
priority: 200
match:
  all:
    - field: tag
      regex: "^devname="
field_map:
  src: { to: src_endpoint.ip, type: ip }
  spt: { to: src_endpoint.port, type: port }
  dst: { to: dst_endpoint.ip, type: ip }
  dpt: { to: dst_endpoint.port, type: port }
  action:
    to: activity_id
    type: enum
    values: { accept: 1, deny: 5 }
    default: 6
defaults: { activity_id: 6, severity_id: 1 }
```

Then reload:

```powershell
py -3 -m cli.main reload
```

No Python file changes are required for a new source on an existing format. `tests/test_plugin_onboarding.py` proves this by adding a Fortigate mapping at test time.

## Docker

Build:

```bash
docker build -t ulpf .
```

Air-gap processing proof:

```bash
docker run --rm --network none \
  -v "$PWD/storage_data:/app/storage_data" \
  -v "$PWD/samples:/app/samples:ro" \
  ulpf python -m cli.main process /app/samples/paloalto_cef.log
```

API demo:

```bash
docker run --rm -p 8000:8000 -p 5514:5514/udp \
  -v "$PWD/storage_data:/app/storage_data" ulpf
```

The UDP listener is an inbound bind, not an outbound network call, and does not violate the air-gap requirement.

No outbound runtime intent check:

```bash
grep -rn "requests\|urllib\|http://\|https://" --include="*.py" .
```

Expected runtime hit is only the Docker healthcheck's localhost `urllib` command; schema fetching is dev-time only.

## Known Limitations

- The committed validator is a trimmed OCSF subset, not the full official schema bundle.
- `/events` uses linear NDJSON scanning. That is acceptable for prototype/demo scale; production should sink to a SIEM/search platform.
- The benchmark script is simple and local; record your own measured number on the demo machine.
- Official OCSF schema fetching remains the main hardening task before final submission.
