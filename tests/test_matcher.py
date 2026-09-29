import pytest
import yaml

from mappings.loader import ULPFSafeLoader, load_mappings
from schema.transforms import TransformError, to_enum


def test_enum_lookup_is_casefolded_and_trimmed():
    spec = {"values": {"Built": 1, 6: 6}, "default": 99}
    assert to_enum(" built ", spec) == 1
    assert to_enum(6, spec) == 6
    assert to_enum("6", spec) == 6
    assert to_enum("unknown", spec) == 99


def test_enum_fold_collision_is_rejected():
    with pytest.raises(ValueError, match="Built.*built|built.*Built"):
        load_mappings(_mapping_dir({"values": {"Built": 1, "built": 2}}))


def test_yaml_boolean_words_and_integer_keys_keep_their_types():
    parsed = yaml.load("on: 1\nno: 2\n6: 3\ntrue: 4\n", Loader=ULPFSafeLoader)
    assert parsed == {"on": 1, "no": 2, 6: 3, True: 4}


def _mapping_dir(values):
    from pathlib import Path
    import tempfile

    directory = Path(tempfile.mkdtemp())
    (directory / "mapping.yaml").write_text(
        "source: test\nformat: json\nfield_map:\n  action:\n    to: activity_id\n    type: enum\n    values: " + yaml.safe_dump(values["values"], default_flow_style=True),
        encoding="utf-8",
    )
    return directory
