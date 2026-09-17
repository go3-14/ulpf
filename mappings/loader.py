from __future__ import annotations

import pathlib

import yaml
from jsonschema import validate as validate_schema

from mappings.mapping_schema import MAPPING_SCHEMA

MAPPINGS_DIR = pathlib.Path(__file__).parent


def load_mappings(directory: str | pathlib.Path | None = None) -> dict:
    path = pathlib.Path(directory) if directory else MAPPINGS_DIR
    registry = {}
    for config_path in sorted(path.glob("*.yaml")):
        with config_path.open(encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        validate_schema(config, MAPPING_SCHEMA)
        if config["source"] in registry:
            raise ValueError(f"duplicate source id: {config['source']}")
        registry[config["source"]] = config
    return registry
