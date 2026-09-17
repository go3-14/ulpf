from __future__ import annotations

import logging
import socket
import threading

from config import UDP_HOST, UDP_PORT
from ingest.pipeline import process
from storage.failed import store_failed
from storage.writer import flush_all

logger = logging.getLogger("ulpf.ingest.syslog_listener")


def listen(host=UDP_HOST, port=UDP_PORT, stop_event=None):
    stop_event = stop_event or threading.Event()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.25)
    sock.bind((host, port))
    logger.info("UDP listener bound to %s:%s", host, port)
    try:
        while not stop_event.is_set():
            try:
                data, _address = sock.recvfrom(65535)
            except socket.timeout:
                continue
            try:
                process(data)
            except Exception as exc:
                logger.exception("unexpected UDP processing error")
                store_failed(data, str(exc))
    finally:
        sock.close()
        flush_all()
