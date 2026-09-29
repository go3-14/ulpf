def test_writer_fsync_modes(tmp_path, monkeypatch):
    import config
    import storage.writer as writer_module
    calls = []
    monkeypatch.setattr(writer_module.os, "fsync", lambda fd: calls.append(fd))
    monkeypatch.setattr(config, "ULPF_FSYNC", "every", raising=False)
    writer = writer_module.PartitionedNDJSONWriter(base_dir=tmp_path / "every", subfolder="raw")
    writer.write("src", {"x": 1})
    assert calls
    writer.close_all()

    calls.clear()
    monkeypatch.setattr(config, "ULPF_FSYNC", "off", raising=False)
    writer = writer_module.PartitionedNDJSONWriter(base_dir=tmp_path / "off", subfolder="raw")
    writer.write("src", {"x": 1})
    writer.flush_all()
    writer.close_all()
    assert calls == []
