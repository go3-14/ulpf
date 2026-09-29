import hashlib

from ingest.context import IngestContext


def event_id_for(raw_bytes: bytes, ctx: IngestContext) -> str:
    """Return a deterministic identifier for file/CLI input and a unique one for network input."""
    if ctx.origin in {"file", "cli"}:
        discriminator = f"{ctx.origin}|{ctx.origin_id}|{ctx.offset if ctx.offset is not None else 0}"
    else:
        discriminator = f"{ctx.origin}|{ctx.received_ms}|{ctx.seq}"
    return hashlib.sha256(discriminator.encode("utf-8") + b"\0" + raw_bytes).hexdigest()
