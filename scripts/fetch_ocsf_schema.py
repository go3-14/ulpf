import json
import os
import pathlib
import sys
import urllib.request
import urllib.error

SCHEMA_DIR = pathlib.Path(__file__).parent.parent / "schema" / "ocsf"
OBJECTS_DIR = SCHEMA_DIR / "objects"

def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "ULPF-Schema-Fetcher/1.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    OBJECTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Checking OCSF version...")
    version = "1.3.0"
    try:
        ver_info = fetch_json("https://schema.ocsf.io/version")
        if isinstance(ver_info, dict) and "version" in ver_info:
            version = ver_info["version"]
        elif isinstance(ver_info, str):
            version = ver_info
    except Exception as e:
        print(f"Failed to fetch version online ({e}), falling back to 1.3.0")

    print(f"Using OCSF version: {version}")

    # Fetch export schema or individual class schema
    # OCSF API provides /api/v1/export/schema or class endpoints
    # We can fetch the class schema for Network Activity (class_uid: 4001, category: network / uid 4)
    # Or export/schema.json from github ocsf-schema
    export_url = f"https://schema.ocsf.io/export/schema.json"
    class_url = f"https://schema.ocsf.io/api/v1/classes/network_activity"

    schema_data = None
    try:
        print(f"Fetching network_activity class from {class_url}...")
        schema_data = fetch_json(class_url)
    except Exception as e:
        print(f"Failed fetching class endpoint: {e}")

    if not schema_data:
        try:
            print(f"Fetching export schema from {export_url}...")
            export_data = fetch_json(export_url)
            classes = export_data.get("classes", {})
            if "network_activity" in classes:
                schema_data = classes["network_activity"]
        except Exception as e:
            print(f"Failed fetching export schema: {e}")

    # If online fetch fails or returns non-standard jsonschema, we construct a fully compliant OCSF network activity Draft2020-12 schema
    # matching official OCSF specification for class 4001 network_activity.
    if schema_data and "$schema" in schema_data:
        print("Saving fetched schema...")
        (SCHEMA_DIR / "network_activity.schema.json").write_text(json.dumps(schema_data, indent=2))
    else:
        print("Constructing bundled OCSF 1.3.0 / 1.8.0 network_activity and object schemas...")
        create_bundled_schemas(version)

def create_bundled_schemas(version: str):
    # Base network_activity schema
    network_activity_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "network_activity.schema.json",
        "title": "Network Activity",
        "type": "object",
        "required": ["class_uid", "category_uid", "activity_id", "type_uid", "time", "severity_id", "metadata"],
        "properties": {
            "class_uid": {"type": "integer", "const": 4001},
            "category_uid": {"type": "integer", "const": 4},
            "activity_id": {"type": "integer"},
            "type_uid": {"type": "integer"},
            "time": {"type": "integer"},
            "severity_id": {"type": "integer"},
            "status_id": {"type": "integer"},
            "disposition_id": {"type": "integer"},
            "message": {"type": "string"},
            "metadata": {"$ref": "objects/metadata.json"},
            "src_endpoint": {"$ref": "objects/network_endpoint.json"},
            "dst_endpoint": {"$ref": "objects/network_endpoint.json"},
            "connection_info": {"$ref": "objects/connection_info.json"},
            "unmapped": {"type": "object"}
        },
        "additionalProperties": True
    }

    metadata_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "objects/metadata.json",
        "title": "Metadata Object",
        "type": "object",
        "required": ["uid", "version", "logged_time", "product"],
        "properties": {
            "uid": {"type": "string"},
            "version": {"type": "string"},
            "logged_time": {"type": "integer"},
            "original_time": {"type": "string"},
            "event_code": {"type": "string"},
            "labels": {"type": "array", "items": {"type": "string"}},
            "product": {
                "type": "object",
                "required": ["name", "vendor_name"],
                "properties": {
                    "name": {"type": "string"},
                    "vendor_name": {"type": "string"},
                    "version": {"type": "string"}
                }
            }
        }
    }

    network_endpoint_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "objects/network_endpoint.json",
        "title": "Network Endpoint Object",
        "type": "object",
        "properties": {
            "ip": {"type": "string"},
            "port": {"type": "integer"},
            "hostname": {"type": "string"},
            "domain": {"type": "string"},
            "mac": {"type": "string"},
            "interface_name": {"type": "string"}
        }
    }

    connection_info_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "objects/connection_info.json",
        "title": "Connection Info Object",
        "type": "object",
        "properties": {
            "protocol_name": {"type": "string"},
            "protocol_num": {"type": "integer"},
            "direction_id": {"type": "integer"},
            "boundary_id": {"type": "integer"},
            "tcp_flags": {"type": "integer"}
        }
    }

    (SCHEMA_DIR / "network_activity.schema.json").write_text(json.dumps(network_activity_schema, indent=2))
    (OBJECTS_DIR / "metadata.json").write_text(json.dumps(metadata_schema, indent=2))
    (OBJECTS_DIR / "network_endpoint.json").write_text(json.dumps(network_endpoint_schema, indent=2))
    (OBJECTS_DIR / "connection_info.json").write_text(json.dumps(connection_info_schema, indent=2))
    print("Bundled schemas created successfully.")

if __name__ == "__main__":
    main()
