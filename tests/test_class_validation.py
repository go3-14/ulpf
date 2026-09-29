import pytest
from schema.validate import validate_event


def test_class_3002_is_validated_and_typos_rejected():
    event = {"class_uid": 3002, "category_uid": 3, "activity_id": 1, "type_uid": 300201,
             "severity_id": 1, "time": 1, "metadata": {"uid": "e"}}
    validate_event(event)
    event["typo_field"] = True
    with pytest.raises(ValueError):
        validate_event(event)
