import glob
import pathlib

import yaml
from jsonschema import validate as js_validate

from mappings.mapping_schema import MAPPING_SCHEMA


MAPPINGS_DIR = pathlib.Path(__file__).parent


def load_mappings(directory: str | pathlib.Path | None = None) -> dict:
    d = pathlib.Path(directory) if directory else MAPPINGS_DIR
    registry = {}
    for f in sorted(glob.glob(str(d / "*.yaml"))):
        with open(f, encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle)
        js_validate(cfg, MAPPING_SCHEMA)
        if cfg["source"] in registry:
            raise ValueError(f"duplicate source id: {cfg['source']} in {f}")
        registry[cfg["source"]] = cfg
    return registry
