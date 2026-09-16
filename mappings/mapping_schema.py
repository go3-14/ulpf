MAPPING_SCHEMA = {
    "type": "object",
    "required": ["source", "format", "field_map"],
    "properties": {
        "source": {"type": "string", "minLength": 1},
        "format": {"enum": ["syslog", "cef", "leef", "json"]},
        "description": {"type": "string"},
        "priority": {"type": "integer"},
        "ocsf": {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "class_uid": {"type": "integer"},
                "category_uid": {"type": "integer"},
            },
        },
        "match": {"type": "object"},
        "constants": {"type": "object"},
        "time": {"type": "object"},
        "defaults": {"type": "object"},
        "field_map": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "required": ["to", "type"],
                "properties": {
                    "to": {"type": "string"},
                    "type": {"enum": ["str", "int", "float", "bool", "ip", "port", "enum", "epoch_ms"]},
                    "values": {"type": "object"},
                    "default": {},
                },
                "allOf": [
                    {
                        "if": {"properties": {"type": {"const": "enum"}}},
                        "then": {"required": ["values"]},
                    }
                ],
            },
        },
    },
}
