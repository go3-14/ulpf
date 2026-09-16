import logging
import socket
import threading

from config import UDP_HOST, UDP_PORT
from ingest import pipeline


logger = logging.getLogger("ulpf.ingest.syslog_listener")


def listen(host=UDP_HOST, port=UDP_PORT, stop_event: threading.Event | None = None):
    stop_event = stop_event or threading.Event()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))
        sock.settimeout(1.0)
        logger.info("UDP syslog listener bound on %s:%s", host, port)
        while not stop_event.is_set():
            try:
                data, _addr = sock.recvfrom(65535)
            except socket.timeout:
                continue
            except Exception:
                logger.error("UDP listener error", exc_info=True)
                continue
            try:
                pipeline.process(data)
            except Exception:
                logger.error("unexpected UDP ingestion error", exc_info=True)
