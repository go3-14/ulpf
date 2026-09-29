from mappings.matcher import condition_matches


def test_condition_operators_and_combinators():
    parsed = {"action": "Denied connection", "kind": "fw", "n": 3}
    assert condition_matches({"field": "action", "startswith": "Denied"}, parsed)
    assert condition_matches({"field": "action", "contains": "connection"}, parsed)
    assert condition_matches({"field": "kind", "in": ["fw", "ids"]}, parsed)
    assert condition_matches({"field": "n", "exists": True}, parsed)
    assert condition_matches({"all": [{"field": "kind", "equals": "fw"}, {"field": "n", "exists": True}]}, parsed)
    assert not condition_matches({"not": {"field": "kind", "equals": "fw"}}, parsed)
