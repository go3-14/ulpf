import json
from pathlib import Path


def test_class_manifest_includes_required_classes():
    manifest = json.loads(Path("schema/ocsf/manifest.json").read_text(encoding="utf-8"))
    classes = manifest["classes"]
    for class_uid in (0, 3002, 4001, 4002, 6003):
        assert str(class_uid) in classes
        assert Path("schema/ocsf", classes[str(class_uid)]["file"]).exists()
