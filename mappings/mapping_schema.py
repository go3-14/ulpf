MAPPING_SCHEMA = {
    "type": "object",
    "required": ["source", "format", "field_map"],
    "properties": {
        "source": {"type": "string"},
        "format": {"type": "string", "enum": ["syslog", "syslog5424", "cef", "leef", "json", "xml", "csv", "text"]},
        "version": {"type": "string"},
        "description": {"type": "string"},
        "ocsf": {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "class_uid": {"type": "integer"},
                "category_uid": {"type": "integer"}
            }
        },
        "priority": {"type": "integer"},
        "match": {
            "type": "object",
            "properties": {
                "all": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["field"],
                        "properties": {
                            "field": {"type": "string"},
                            "regex": {"type": "string"},
                            "equals": {"type": "string"},
                            "contains": {"type": "string"}
                        }
                    }
                }
            }
        },
        "constants": {"type": "object"},
        "time": {
            "type": "object",
            "properties": {
                "field": {"type": "string"},
                "formats": {"type": "array", "items": {"type": "string"}},
                "assume_year": {"type": "string"},
                "timezone": {"type": "string"}
            }
        },
        "field_map": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "required": ["to", "type"],
                "properties": {
                    "to": {"type": "string"},
                    "type": {"type": "string", "enum": ["str", "int", "float", "bool", "ip", "port", "enum", "epoch_ms"]},
                    "values": {"type": "object"},
                    "default": {}
                }
            }
        },
        "defaults": {"type": "object"},
        "extract": {"type": "array", "items": {"type": "object"}}
        ,"variants": {"type": "array", "items": {"type": "object"}}
    },
    "additionalProperties": True
}
