import time as _time


def build_base(config: dict, event_id: str) -> dict:
    """Build a fresh OCSF base dict for each event."""
    ocsf = config.get("ocsf", {})
    now_ms = int(_time.time() * 1000)
    return {
        "class_uid": ocsf.get("class_uid", 4001),
        "category_uid": ocsf.get("category_uid", 4),
        "metadata": {
            "uid": event_id,
            "version": str(ocsf.get("version", "subset-1")),
            "logged_time": now_ms,
            "product": {"name": "ULPF", "vendor_name": "ULPF"},
            "labels": ["ulpf"],
        },
    }
