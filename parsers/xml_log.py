import xml.etree.ElementTree as ET

def parse_xml(raw_log: str) -> dict | None:
    if "<!doctype" in raw_log.lower() or "<!entity" in raw_log.lower():
        return None
    try:
        root = ET.fromstring(raw_log.strip())
    except ET.ParseError:
        return None
    out = {}
    def visit(node, path):
        tag = node.tag.rsplit('}', 1)[-1]
        current = f"{path}.{tag}" if path else tag
        for key, value in node.attrib.items():
            out[f"{current}@{key.rsplit('}', 1)[-1]}"] = value
        if node.text and node.text.strip(): out[current] = node.text.strip()
        for child in node: visit(child, current)
    visit(root, "")
    out.setdefault("event_type", root.tag.rsplit('}', 1)[-1])
    return out
