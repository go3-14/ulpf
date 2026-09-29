import glob
import hashlib
import pathlib
import re
import yaml
from jsonschema import validate as js_validate
from mappings.mapping_schema import MAPPING_SCHEMA
from schema.transforms import compile_enum_values


class ULPFSafeLoader(yaml.SafeLoader):
    """YAML loader with YAML 1.2 boolean words rather than YAML 1.1 words."""


ULPFSafeLoader.yaml_implicit_resolvers = {
    key: [resolver for resolver in resolvers if resolver[0] != "tag:yaml.org,2002:bool"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
ULPFSafeLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|false)$", re.IGNORECASE),
    list("tTfF"),
)

MAPPINGS_DIR = pathlib.Path(__file__).parent.resolve()

class MappingSpec(dict):
    @property
    def id(self):
        return self.get("source")
    @property
    def version(self):
        return self.get("version", "1")
    @property
    def sha256(self):
        return self.get("sha256")

def load_mappings(directory: str | pathlib.Path | None = None) -> dict:
    d = pathlib.Path(directory) if directory else MAPPINGS_DIR
    registry = {}
    for f in sorted(glob.glob(str(d / "*.yaml"))):
        raw = pathlib.Path(f).read_bytes()
        cfg = yaml.load(raw.decode("utf-8"), Loader=ULPFSafeLoader)
        if not isinstance(cfg, dict):
            continue
        js_validate(cfg, MAPPING_SCHEMA)
        cfg = MappingSpec(cfg)
        cfg.setdefault("version", "1")
        cfg["sha256"] = hashlib.sha256(raw).hexdigest()
        for spec in (cfg.get("field_map") or {}).values():
            if spec.get("type") == "enum":
                spec["_folded_values"] = compile_enum_values(spec.get("values") or {})
        if cfg["source"] in registry:
            raise ValueError(f"duplicate source id: {cfg['source']} in {f}")
        registry[cfg["source"]] = cfg
    return registry
