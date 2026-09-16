# ULPF Simple Prototype

This branch proves the core idea without a database, web server, queue, or external Python package:

```text
raw network-device log → parse → common event JSON → raw + normalized JSONL files
```

It supports perimeter logs in Syslog, CEF, LEEF, and JSON. Run it with Python 3.11+:

```powershell
python simple_ulpf.py process samples/cisco_asa_syslog.log
```

Each valid line prints `OK <event id> <source>`. The program writes:

```text
output/raw.jsonl          # byte-identical input in Base64, keyed by event_id
output/normalized.jsonl   # common schema, keyed by the same event_id
```

To show the forensic pair:

```powershell
python simple_ulpf.py show <event-id>
```

## How it satisfies the statement

| Requirement | Simple proof |
| --- | --- |
| a, d | Raw bytes are Base64-preserved in `raw.jsonl`; `raw_ref` and `event_id` link the pair. |
| b | Four small stdlib parsers extract source fields. |
| c | Every event uses `source`, `network`, `activity`, `time`, and `unmapped`. |
| e, i | Add a source entry and mappings in `sources.json`; no parser changes for an existing format. |
| f | Every input produces the same JSON layout, ready for one common view. |
| g | JSONL is a standard streaming/data-lake exchange format. |
| h | Ports are integers and fields are stable across vendors. |
| j | The runtime uses only Python's standard library and makes no network calls. |
| k | The small Dockerfile packages the same CLI. |

`unmapped` keeps parsed attributes that are not yet part of the common schema. This is the safe place to extend the prototype later.

## Add a source without code

Add a new object to `sources.json` for a device using an existing format. Its `map` block tells ULPF which parsed fields become common fields. This keeps vendor-specific choices out of the program.

## Test

```powershell
python -m pytest tests/test_simple_ulpf.py -q
```

## Container / air-gapped run

```bash
docker build -t ulpf-simple .
docker run --rm --network none -v "$PWD/output:/data" -v "$PWD/samples:/samples:ro" ulpf-simple process /samples/paloalto_cef.log
```

The prototype intentionally does not claim billions-of-events throughput. Its production path is straightforward: place a queue before several stateless instances and send the JSONL stream to a SIEM or data lake.
