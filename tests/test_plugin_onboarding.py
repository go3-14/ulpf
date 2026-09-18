import pathlib
import shutil
import yaml
from ingest.pipeline import process, reload_mappings
from storage.normalized_store import search_normalized

def test_plugin_onboarding(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", tmp_path / "storage")
    import storage.raw_store
    import storage.normalized_store
    import storage.index
    storage.raw_store.reset_writers()
    storage.normalized_store.reset_writers()
    storage.index._index_loaded = False
    storage.index._index_map.clear()


    # 1. Prepare temp mappings directory with base YAMLs
    mappings_src = pathlib.Path(__file__).parent.parent / "mappings"
    mappings_tmp = tmp_path / "mappings"
    shutil.copytree(mappings_src, mappings_tmp)

    # 2. Add brand-new Fortigate YAML dynamically with ZERO python code changes
    fortigate_yaml = {
        "source": "fortigate_syslog_dynamic",
        "format": "syslog",
        "description": "Fortigate Firewall via syslog",
        "ocsf": {"version": "1.9.0", "class_uid": 4001, "category_uid": 4},
        "priority": 100,
        "match": {
            "all": [
                {"field": "message", "contains": "devname=FG100D"}
            ]
        },
        "constants": {
            "metadata.product.vendor_name": "Fortinet",
            "metadata.product.name": "FortiGate",
            "connection_info.direction_id": 0,
        },
        "field_map": {
            "src": {"to": "src_endpoint.ip", "type": "ip"},
            "spt": {"to": "src_endpoint.port", "type": "port"},
            "dst": {"to": "dst_endpoint.ip", "type": "ip"},
            "dpt": {"to": "dst_endpoint.port", "type": "port"},
            "proto": {"to": "connection_info.protocol_name", "type": "str"}
        },
        "defaults": {"activity_id": 6, "severity_id": 1}
    }
    with open(mappings_tmp / "fortigate_syslog.yaml", "w", encoding="utf-8") as f:
        yaml.dump(fortigate_yaml, f)

    # 3. Reload mappings
    count = reload_mappings(mappings_tmp)
    assert count >= 5

    # 4. Ingest Fortigate log line
    forti_line = b"<189>date=2026-01-10 time=10:00:00 devname=FG100D devid=FG100D3G15800001 logid=0000000013 type=traffic src=192.168.1.99 spt=50000 dst=10.0.0.1 dpt=80 proto=6"
    forti_id = process(forti_line)
    assert forti_id is not None

    # Verify routing to fortigate_syslog
    forti_events = search_normalized(source="fortigate_syslog_dynamic")
    assert len(forti_events) == 1
    assert forti_events[0]["metadata"]["product"]["vendor_name"] == "Fortinet"

    # 5. Verify Cisco ASA line still routes to cisco_asa without regression
    asa_line = b"<134>Jan 10 10:00:00 fw01 %ASA-6-302013: Built inbound TCP connection 12345 for outside:192.168.1.50/49152 to inside:10.0.0.5/80"
    asa_id = process(asa_line)
    assert asa_id is not None
    asa_events = search_normalized(source="cisco_asa")
    assert len(asa_events) >= 1

    # Restore default mappings directory
    reload_mappings()

def test_all_four_sample_formats_ingest(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", tmp_path / "storage")
    import storage.raw_store
    import storage.normalized_store
    import storage.index
    storage.raw_store.reset_writers()
    storage.normalized_store.reset_writers()
    storage.index._index_loaded = False
    storage.index._index_map.clear()
    reload_mappings()


    samples_dir = pathlib.Path(__file__).parent.parent / "samples"
    sample_files = [
        "cisco_asa_syslog.log",
        "paloalto_cef.log",
        "generic_leef.log",
        "generic_json.log"
    ]

    total_ingested = 0
    for sfile in sample_files:
        fpath = samples_dir / sfile
        with open(fpath, "rb") as f:
            for line in f.read().splitlines():
                if not line.strip():
                    continue
                eid = process(line)
                if eid:
                    total_ingested += 1

    assert total_ingested >= 10
    all_events = search_normalized(limit=100)
    assert len(all_events) == total_ingested
