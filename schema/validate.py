"""Offline OCSF Network Activity validation using only bundled schema files."""

from __future__ import annotations

import json
import pathlib
from functools import lru_cache

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


SCHEMA_DIR = pathlib.Path(__file__).parent / "ocsf"


@lru_cache(maxsize=1)
def _load_bundle() -> tuple[dict, Registry]:
    manifest_path = SCHEMA_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    registry = Registry()
    root: dict | None = None

    for resource_info in manifest["resources"]:
        path = SCHEMA_DIR / resource_info["path"]
        document = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(document, default_specification=DRAFT202012)
        # Register using the canonical fetched URI.  This is what the bundled
        # documents use in absolute $ref values; $id supplies relative-ref bases.
        registry = registry.with_resource(resource_info["uri"], resource)
        declared_uri = document.get("$id")
        if isinstance(declared_uri, str) and declared_uri != resource_info["uri"]:
            registry = registry.with_resource(declared_uri, resource)
        if resource_info["uri"] == manifest["root_uri"]:
            root = document

    if root is None:
        raise ValueError("OCSF bundle manifest does not include its root schema")
    return root, registry


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema, registry = _load_bundle()
    return Draft202012Validator(schema, registry=registry)


def validate_event(event: dict) -> None:
    """Raise ValueError with the first readable OCSF validation failure."""
    errors = sorted(_validator().iter_errors(event), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        path = ".".join(map(str, error.path)) or "<root>"
        raise ValueError(f"OCSF validation failed at {path}: {error.message}")
