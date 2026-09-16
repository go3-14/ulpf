import json
import pathlib

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


SCHEMA_DIR = pathlib.Path(__file__).parent / "ocsf"


def _build_registry() -> Registry:
    registry = Registry()
    for path in SCHEMA_DIR.rglob("*.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        uri = doc.get("$id") or path.name
        registry = registry.with_resource(uri, Resource.from_contents(doc))
    return registry


_schema = json.loads((SCHEMA_DIR / "network_activity.schema.json").read_text(encoding="utf-8"))
_validator = Draft202012Validator(_schema, registry=_build_registry())


def validate_event(event: dict) -> None:
    """Raises ValueError with a readable path on validation failure."""
    errors = sorted(_validator.iter_errors(event), key=lambda e: e.path)
    if errors:
        e = errors[0]
        path = ".".join(map(str, e.path)) or "<root>"
        raise ValueError(f"OCSF validation failed at {path}: {e.message}")
