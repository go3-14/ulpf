"""Immutable-ish metadata carried with an ingestion attempt."""

from dataclasses import dataclass, field


@dataclass
class IngestContext:
    origin: str
    origin_id: str = ""
    offset: int | None = None
    line_no: int | None = None
    received_ms: int = 0
    reference_ms: int | None = None
    seq: int = 0
    source_hint: str | None = None
    file_state: dict = field(default_factory=dict)
