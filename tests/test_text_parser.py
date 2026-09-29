from parsers.text import parse_text

def test_text_parser_preserves_message():
    assert parse_text("hello")["message"] == "hello"
