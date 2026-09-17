from __future__ import annotations

import shutil

from ingest.pipeline import process, reload_mappings
from mappings.loader import MAPPINGS_DIR
from parsers.syslog import parse_syslog
from storage.normalized_store import get_normalized


def test_new_syslog_source_uses_yaml_only(tmp_path, monkeypatch):
    mapping_dir = tmp_path / "mappings"
    shutil.copytree(MAPPINGS_DIR, mapping_dir)
    (mapping_dir / "fortigate.yaml").write_text(
        """source: fortigate\nformat: syslog\ndescription: Fortigate\nocsf:\n  version: '1.9.0'\n  class_uid: 4001\n  category_uid: 4\npriority: 200\nmatch:\n  all:\n    - field: tag\n      regex: '^devname='\nconstants:\n  connection_info.direction_id: 0\ntime:\n  field: timestamp\n  formats: ['%b %d %H:%M:%S']\n  assume_year: current\nfield_map:\n  src: {to: src_endpoint.ip, type: ip}\n  spt: {to: src_endpoint.port, type: port}\n  dst: {to: dst_endpoint.ip, type: ip}\n  dpt: {to: dst_endpoint.port, type: port}\n  proto: {to: connection_info.protocol_name, type: str}\n  action:\n    to: activity_id\n    type: enum\n    values: {Deny: 5}\n    default: 99\n  severity:\n    to: severity_id\n    type: enum\n    values: {'6': 1}\n    default: 1\ndefaults: {activity_id: 6, severity_id: 1}\n""",
        encoding="utf-8",
    )
    monkeypatch.setattr("ingest.pipeline.MAPPINGS", __import__("mappings.loader", fromlist=["load_mappings"]).load_mappings(mapping_dir))
    line = b"<134>Jan 10 10:00:00 fortigate devname=FG-1: Deny tcp src outside:192.0.2.50/50000 dst inside:198.51.100.50/443\n"
    assert parse_syslog(line.decode())["tag"] == "devname=FG-1"
    event_id = process(line)
    assert event_id
    assert get_normalized(event_id)["metadata"]["labels"][1] == "fortigate"
    asa_id = process(
        b"<166>Apr 27 11:31:23 asa-fw %ASA-6-302013: Built outbound TCP connection 2921 for outside:198.51.100.100/80 to inside:10.1.1.154/58799\n"
    )
    assert asa_id
    assert get_normalized(asa_id)["metadata"]["labels"][1] == "cisco_asa"
    reload_mappings()
