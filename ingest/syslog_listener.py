import logging
import socket
import threading
from config import UDP_HOST, UDP_PORT
from ingest.pipeline import process

logger = logging.getLogger("ulpf.syslog_listener")

def listen(host: str = UDP_HOST, port: int = UDP_PORT, stop_event: threading.Event | None = None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    try:
        sock.bind((host, port))
        logger.info(f"UDP Syslog listener bound to {host}:{port}")
    except Exception as e:
        logger.error(f"Failed to bind UDP listener on {host}:{port}: {e}")
        return

    while stop_event is None or not stop_event.is_set():
        try:
            data, addr = sock.recvfrom(65535)
            if data and data.strip():
                try:
                    process(data.strip())
                except Exception as ex:
                    logger.error(f"Error processing UDP packet from {addr}: {ex}", exc_info=True)
        except socket.timeout:
            continue
        except Exception as e:
            if stop_event and stop_event.is_set():
                break
            logger.error(f"UDP listener socket error: {e}", exc_info=True)

    sock.close()
    logger.info("UDP Syslog listener shutdown cleanly.")
