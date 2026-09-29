from mappings.variants import select_variant


def test_first_matching_variant_overlays_mapping():
    mapping = {"source": "x", "field_map": {"a": {"to": "a", "type": "str"}},
               "variants": [{"id": "auth", "when": {"field": "kind", "equals": "auth"},
                             "class_uid": 3002, "field_map": {"u": {"to": "user.name", "type": "str"}}}]}
    selected = select_variant(mapping, {"kind": "auth"})
    assert selected["ocsf"]["class_uid"] == 3002
    assert "a" in selected["field_map"] and "u" in selected["field_map"]
