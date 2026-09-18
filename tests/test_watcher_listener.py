import socket
import threading
import time

import ingest.watcher as watcher_module
from ingest.syslog_listener import listen


def test_watcher_waits_for_newline_and_does_not_duplicate_partial_bytes(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(watcher_module, "process", lambda line: seen.append(line))
    stop = threading.Event()
    thread = threading.Thread(
        target=watcher_module.watch,
        kwargs={"spool_dir": tmp_path, "poll_interval": 0.05, "stop_event": stop},
        daemon=True,
    )
    thread.start()
    spool_file = tmp_path / "partial.log"
    spool_file.write_bytes(b"first")
    time.sleep(0.12)
    assert seen == []
    with spool_file.open("ab") as handle:
        handle.write(b" event ")
    time.sleep(0.12)
    assert seen == []
    with spool_file.open("ab") as handle:
        handle.write(b"\n")
    deadline = time.time() + 2
    while not seen and time.time() < deadline:
        time.sleep(0.05)
    stop.set()
    thread.join(1)
    assert seen == [b"first event "]


def test_udp_listener_exits_after_stop_event():
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    stop = threading.Event()
    thread = threading.Thread(
        target=listen,
        kwargs={"host": "127.0.0.1", "port": port, "stop_event": stop},
        daemon=True,
    )
    thread.start()
    time.sleep(0.1)
    stop.set()
    thread.join(2)
    assert not thread.is_alive()
