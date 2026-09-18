"""Offline OCSF Network Activity validation using only bundled schema files.

Uses the bundled OCSF 1.9.0 network_activity.json (self-contained with all $defs
inline) for validation. additionalProperties restrictions are stripped before
validation so ULPF extension fields (unmapped, logged_time, etc.) are allowed.

The validator is built once and cached; validate_event() has near-zero overhead
after the first call.
"""
import json
import pathlib
from functools import lru_cache

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

SCHEMA_DIR = pathlib.Path(__file__).parent / "ocsf"
_CLASS_SCHEMA_PATH = SCHEMA_DIR / "classes" / "network_activity.json"
_MANIFEST_PATH = SCHEMA_DIR / "manifest.json"


def _strip_additional_properties(schema: object) -> object:
    """Recursively remove additionalProperties: false from the schema.

    The full OCSF 1.9.0 schema sets additionalProperties: false on every object.
    ULPF adds extension fields (unmapped, logged_time, labels, etc.) that are
    valid per the spec but would be rejected. We validate structure and types only.
    """
    if isinstance(schema, dict):
        cleaned = {k: _strip_additional_properties(v) for k, v in schema.items()
                   if not (k == "additionalProperties" and v is False)}
        return cleaned
    if isinstance(schema, list):
        return [_strip_additional_properties(item) for item in schema]
    return schema


@lru_cache(maxsize=1)
def _get_validator() -> Draft202012Validator:
    """Build and cache the validator from bundled OCSF 1.9.0 schema.

    Prefers the full manifest-based 1.9.0 schema. Falls back to the legacy
    hand-written subset if the classes/ directory is absent.
    """
    if _CLASS_SCHEMA_PATH.exists() and _MANIFEST_PATH.exists():
        manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
        registry = Registry()
        root = None

        for resource_info in manifest["resources"]:
            path = SCHEMA_DIR / resource_info["path"]
            document = json.loads(path.read_text(encoding="utf-8"))
            document = _strip_additional_properties(document)
            resource = Resource.from_contents(document, default_specification=DRAFT202012)
            registry = registry.with_resource(resource_info["uri"], resource)
            declared_uri = document.get("$id")
            if isinstance(declared_uri, str) and declared_uri != resource_info["uri"]:
                registry = registry.with_resource(declared_uri, resource)
            if resource_info["uri"] == manifest["root_uri"]:
                root = document

        if root is None:
            raise ValueError("OCSF bundle manifest does not include its root schema")
        return Draft202012Validator(root, registry=registry)

    # Fallback: legacy hand-written subset schema (documented as subset in README)
    legacy_path = SCHEMA_DIR / "network_activity.schema.json"
    schema = json.loads(legacy_path.read_text(encoding="utf-8"))
    schema = _strip_additional_properties(schema)
    return Draft202012Validator(schema)


def validate_event(event: dict) -> None:
    """Validate a normalized OCSF event dict against the Network Activity schema.

    Raises ValueError with a human-readable dot-path on the first failure.
    Returns None silently on success.
    """
    validator = _get_validator()
    errors = sorted(validator.iter_errors(event), key=lambda e: [str(p) for p in e.path])
    if errors:
        e = errors[0]
        path_str = ".".join(map(str, e.path)) if e.path else "<root>"
        raise ValueError(f"OCSF validation failed at {path_str}: {e.message}")
