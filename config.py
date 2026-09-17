"""Runtime configuration loaded once at process startup."""

from __future__ import annotations

import os
import pathlib

STORAGE_DIR = pathlib.Path(os.environ.get("ULPF_STORAGE_DIR", pathlib.Path(__file__).parent / "storage_data"))
SPOOL_DIR = pathlib.Path(os.environ.get("ULPF_SPOOL_DIR", pathlib.Path(__file__).parent / "spool"))
API_HOST = os.environ.get("ULPF_API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("ULPF_API_PORT", "8000"))
UDP_HOST = os.environ.get("ULPF_UDP_HOST", "0.0.0.0")
UDP_PORT = int(os.environ.get("ULPF_UDP_PORT", "5514"))
LOG_LEVEL = os.environ.get("ULPF_LOG_LEVEL", "INFO").upper()
POLL_INTERVAL = float(os.environ.get("ULPF_POLL_INTERVAL", "1.0"))
