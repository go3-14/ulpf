import pathlib
from ingest.pipeline import process
from storage.raw_store import read_raw
from storage.normalized_store import get_normalized
from schema.validate import validate_event

def test_pipeline_end_to_end_syslog(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", tmp_path)
    import storage.raw_store
    import storage.normalized_store
    import storage.index
    storage.raw_store.reset_writers()
    storage.normalized_store.reset_writers()
    storage.index._index_loaded = False
    storage.index._index_map.clear()


    sample_file = pathlib.Path(__file__).parent.parent / "samples" / "cisco_asa_syslog.log"
    assert sample_file.exists()

    with open(sample_file, "rb") as f:
        lines = [line for line in f.read().splitlines() if line.strip()]

    processed_count = 0
    failed_count = 0

    for line in lines:
        event_id = process(line)
        if event_id is None:
            failed_count += 1
            continue

        processed_count += 1

        # 1. Exact raw byte equality
        retrieved_raw = read_raw(event_id)
        assert retrieved_raw == line, f"Raw bytes mismatch: {retrieved_raw} != {line}"

        # 2. Retrieve normalized event and validate OCSF schema
        event = get_normalized(event_id)
        assert event is not None
        validate_event(event)

        # 3. Structural assertions
        assert event["type_uid"] == event["class_uid"] * 100 + event["activity_id"]
        assert isinstance(event["time"], int)
        assert event["metadata"]["uid"] == event_id

        if "src_endpoint" in event and "port" in event["src_endpoint"]:
            assert isinstance(event["src_endpoint"]["port"], int)

        if "dst_endpoint" in event and "port" in event["dst_endpoint"]:
            assert isinstance(event["dst_endpoint"]["port"], int)

        # 4. Lossless unmapped verification
        assert "unmapped" in event or "_ulpf_transform_errors" in event.get("unmapped", {})

    assert processed_count >= 4
    # Phase 4 fallback mode stores previously-unmapped lines as Base Events.
    assert failed_count == 0
