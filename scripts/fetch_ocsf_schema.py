"""Bundle the pinned OCSF Network Activity JSON Schema for offline validation.

This is a development-time utility.  Application modules must never import it.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import urllib.parse
import urllib.request
from collections import deque


PINNED_OCSF_VERSION = "1.9.0"
SCHEMA_SERVER = f"https://schema.ocsf.io/schema/{PINNED_OCSF_VERSION}"
ROOT_URI = f"{SCHEMA_SERVER}/classes/network_activity"
# An explicitly empty profile selection avoids making optional profiles part of
# the base-event contract while retaining the official Network Activity class.
ROOT_FETCH_URL = f"{ROOT_URI}?profiles="
OUTPUT_DIR = pathlib.Path(__file__).resolve().parents[1] / "schema" / "ocsf"


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url, headers={"User-Agent": "ULPF schema bundler (development only)"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()
    document = json.loads(payload.decode("utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"schema resource is not a JSON object: {url}")
    return document


def _references(value: object) -> set[str]:
    """Return every JSON Schema reference contained in *value*."""
    found: set[str] = set()
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str):
            found.add(ref)
        for child in value.values():
            found.update(_references(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_references(child))
    return found


def _canonical_uri(ref: str, base_uri: str) -> str | None:
    """Resolve an OCSF $ref and remove its JSON Pointer fragment."""
    target, _fragment = urllib.parse.urldefrag(urllib.parse.urljoin(base_uri, ref))
    parsed = urllib.parse.urlparse(target)
    expected = urllib.parse.urlparse(SCHEMA_SERVER)
    if parsed.scheme != expected.scheme or parsed.netloc != expected.netloc:
        return None
    versioned_prefix = f"/schema/{PINNED_OCSF_VERSION}/"
    if parsed.path.startswith(versioned_prefix):
        return target
    # OCSF documents may declare a stable, unversioned $id.  Rebind such
    # references to this bundle's pinned release instead of accidentally
    # following the schema server's moving "latest" resource.
    if parsed.path.startswith("/schema/"):
        relative = parsed.path.removeprefix("/schema/")
        return f"{SCHEMA_SERVER}/{relative}"
    return None


def _relative_path(uri: str) -> pathlib.Path:
    parsed = urllib.parse.urlparse(uri)
    prefix = f"/schema/{PINNED_OCSF_VERSION}/"
    relative = pathlib.PurePosixPath(parsed.path.removeprefix(prefix))
    if not relative.parts or ".." in relative.parts:
        raise ValueError(f"unsafe schema URI: {uri}")
    return pathlib.Path(*relative.parts).with_suffix(".json")


def _write_json(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bundle_schema(output_dir: pathlib.Path = OUTPUT_DIR) -> dict:
    """Fetch the root schema and its full OCSF $ref closure into *output_dir*."""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    pending: deque[tuple[str, str]] = deque([(ROOT_URI, ROOT_FETCH_URL)])
    seen: set[str] = set()
    resources: list[dict[str, str]] = []

    while pending:
        uri, fetch_url = pending.popleft()
        if uri in seen:
            continue
        seen.add(uri)

        document = _fetch_json(fetch_url)
        # $id establishes the base URI used when a validator resolves relative refs.
        document.setdefault("$id", uri)
        target_path = _relative_path(uri)
        _write_json(output_dir / target_path, document)
        resources.append(
            {
                "uri": uri,
                "path": target_path.as_posix(),
                "sha256": hashlib.sha256(
                    json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
                "source_url": fetch_url,
            }
        )

        for ref in _references(document):
            target = _canonical_uri(ref, uri)
            if target is not None and target not in seen:
                pending.append((target, target))

    manifest = {
        "ocsf_version": PINNED_OCSF_VERSION,
        "root_uri": ROOT_URI,
        "resources": sorted(resources, key=lambda item: item["uri"]),
    }
    _write_json(output_dir / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    manifest = bundle_schema()
    print(
        f"Bundled OCSF {manifest['ocsf_version']} with "
        f"{len(manifest['resources'])} schema resources."
    )
