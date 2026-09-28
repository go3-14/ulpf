import xml.etree.ElementTree as ET

def parse_xml(raw_log: str) -> dict | None:
    try:
        root = ET.fromstring(raw_log.strip())
    except ET.ParseError:
        return None
    out = dict(root.attrib)
    for node in root.iter():
        if node is root:
            continue
        key = node.tag.rsplit('}', 1)[-1]
        if node.text and node.text.strip():
            out[key] = node.text.strip()
        out.update({k.rsplit('}', 1)[-1]: v for k, v in node.attrib.items()})
    out.setdefault("event_type", root.tag.rsplit('}', 1)[-1])
    return out
