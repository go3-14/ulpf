import logging
import socket
import threading
import ssl
from ingest.queue import IngestionQueue
from config import UDP_HOST, UDP_PORT
from ingest.pipeline import process
from storage.failed import store_failed
from storage.writer import flush_all

logger = logging.getLogger("ulpf.syslog_listener")

def listen(host: str = UDP_HOST, port: int = UDP_PORT, stop_event: threading.Event | None = None,
           tcp_port: int | None = None, tls_cert: str | None = None, tls_key: str | None = None,
           queue_size: int = 10000):
    ingest_queue = IngestionQueue(queue_size).start()
    tcp_sock = None
    tcp_thread = None
    if tcp_port:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_sock.settimeout(1.0)
        tcp_sock.bind((host, tcp_port)); tcp_sock.listen(32)
        logger.info("TCP syslog listener bound to %s:%s%s", host, tcp_port, " with TLS" if tls_cert else "")
        context = None
        if tls_cert:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(tls_cert, tls_key)
        def accept_tcp():
            while stop_event is None or not stop_event.is_set():
                try: conn, _ = tcp_sock.accept()
                except socket.timeout: continue
                except OSError: break
                try:
                    if context: conn = context.wrap_socket(conn, server_side=True)
                    with conn:
                        buf = b""
                        while True:
                            chunk = conn.recv(65535)
                            if not chunk: break
                            buf += chunk
                            while b"\n" in buf:
                                line, buf = buf.split(b"\n", 1)
                                if line.strip(): ingest_queue.put(line.strip())
                        if buf.strip(): ingest_queue.put(buf.strip())
                except Exception as ex:
                    logger.warning("TCP syslog connection failed: %s", ex)
        tcp_thread = threading.Thread(target=accept_tcp, daemon=True)
        tcp_thread.start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    try:
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
                        ingest_queue.put(data.strip())
                    except Exception as ex:
                        logger.error(f"Error processing UDP packet from {addr}: {ex}", exc_info=True)
                        store_failed(data, str(ex))
            except socket.timeout:
                continue
            except Exception as e:
                if stop_event and stop_event.is_set():
                    break
                logger.error(f"UDP listener socket error: {e}", exc_info=True)
    finally:
        sock.close()
        if tcp_sock:
            tcp_sock.close()
        if tcp_thread:
            tcp_thread.join(timeout=2)
        ingest_queue.close()
        flush_all()
        logger.info("UDP Syslog listener shutdown cleanly.")
