from mappings.extract import apply_extracts


def test_extract_kv_preserves_duplicate_keys():
    parsed = {"message": 'a=1 b="two words" a=3'}
    apply_extracts(parsed, [{"type": "kv", "field": "message"}])
    assert parsed["a"] == "1"
    assert parsed["a__2"] == "3"
    assert parsed["b"] == "two words"


def test_extract_split_and_json():
    parsed = {"message": '{"x":{"y":2}}', "csv": "a,\"b,c\""}
    apply_extracts(parsed, [{"type": "json", "field": "message", "prefix": "j_"},
                            {"type": "split", "field": "csv", "params": {"sep": ",", "names": ["a", "b"], "csv": True}}])
    assert parsed["j_x.y"] == 2
    assert parsed["a"] == "a"
    assert parsed["b"] == "b,c"
