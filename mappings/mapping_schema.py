MAPPING_SCHEMA = {
    "type": "object",
    "required": ["source", "format", "field_map"],
    "properties": {
        "source": {"type": "string"},
        "format": {"enum": ["syslog", "cef", "leef", "json"]},
        "field_map": {"type": "object"},
    },
}
