import os
from pathlib import Path


STORAGE_DIR = Path(os.environ.get("ULPF_STORAGE_DIR", "storage_data"))
SPOOL_DIR = Path(os.environ.get("ULPF_SPOOL_DIR", "spool"))
API_HOST = os.environ.get("ULPF_API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("ULPF_API_PORT", "8000"))
UDP_HOST = os.environ.get("ULPF_UDP_HOST", "0.0.0.0")
UDP_PORT = int(os.environ.get("ULPF_UDP_PORT", "5514"))
LOG_LEVEL = os.environ.get("ULPF_LOG_LEVEL", "INFO")
OCSF_VERSION = os.environ.get("ULPF_OCSF_VERSION", "subset-1")
