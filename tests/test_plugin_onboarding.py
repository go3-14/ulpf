import shutil
from pathlib import Path

from ingest import pipeline
from storage.normalized_store import read_normalized


FORTIGATE_YAML = """
source: fortigate_syslog
format: syslog
description: "Fortigate via syslog"
ocsf: { version: "subset-1", class_uid: 4001, category_uid: 4 }
priority: 200
match:
  all:
    - field: tag
      regex: "^devname="
constants:
  metadata.product.vendor_name: "Fortinet"
  metadata.product.name: "FortiGate"
time:
  field: timestamp
  formats: ["%b %d %H:%M:%S"]
  assume_year: current
field_map:
  src: { to: src_endpoint.ip, type: ip }
  spt: { to: src_endpoint.port, type: port }
  dst: { to: dst_endpoint.ip, type: ip }
  dpt: { to: dst_endpoint.port, type: port }
  proto: { to: connection_info.protocol_name, type: str }
  action:
    to: activity_id
    type: enum
    values: { accept: 1, deny: 5 }
    default: 6
defaults: { activity_id: 6, severity_id: 1 }
"""


def test_new_syslog_source_by_yaml_only(tmp_path):
    mappings = tmp_path / "mappings"
    shutil.copytree("mappings", mappings)
    (mappings / "fortigate.yaml").write_text(FORTIGATE_YAML, encoding="utf-8")
    try:
        pipeline.reload_mappings(mappings)
        raw = b"<134>Jan 10 10:00:00 fg devname=fortigate: action=accept src=192.0.2.1 spt=1111 dst=198.51.100.1 dpt=443 proto=tcp\n"
        event_id = pipeline.process(raw)
        assert event_id
        event = read_normalized(event_id)
        assert event["metadata"]["labels"][1] == "fortigate_syslog"
        assert pipeline.process(Path("samples/cisco_asa_syslog.log").read_bytes().splitlines(True)[0])
    finally:
        pipeline.reload_mappings()
