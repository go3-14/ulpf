import os
import pathlib

# Base directory paths
BASE_DIR = pathlib.Path(__file__).parent.resolve()

STORAGE_DIR = pathlib.Path(os.environ.get("ULPF_STORAGE_DIR", BASE_DIR / "storage_data")).resolve()
SPOOL_DIR = pathlib.Path(os.environ.get("ULPF_SPOOL_DIR", BASE_DIR / "spool")).resolve()

# Network / Server Configuration
API_HOST = os.environ.get("ULPF_API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("ULPF_API_PORT", "8000"))

UDP_HOST = os.environ.get("ULPF_UDP_HOST", "0.0.0.0")
UDP_PORT = int(os.environ.get("ULPF_UDP_PORT", "5514"))
TCP_PORT = int(os.environ.get("ULPF_TCP_PORT", "0")) or None
TLS_CERT = os.environ.get("ULPF_TLS_CERT")
TLS_KEY = os.environ.get("ULPF_TLS_KEY")

LOG_LEVEL = os.environ.get("ULPF_LOG_LEVEL", "INFO")
POLL_INTERVAL = float(os.environ.get("ULPF_POLL_INTERVAL", "1.0"))
NORMALIZED_CACHE_MAX = int(os.environ.get("ULPF_NORMALIZED_CACHE_MAX", "10000"))
ULPF_FSYNC = os.environ.get("ULPF_FSYNC", "batch").lower()
if ULPF_FSYNC not in {"off", "batch", "every"}:
    raise ValueError("ULPF_FSYNC must be off, batch, or every")
