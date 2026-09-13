import xml.etree.ElementTree as ET
from normalisation.event import NormalizedEvent


def parse(log):

    root = ET.fromstring(log)

    return NormalizedEvent(
        event_type=root.findtext("type"),
        timestamp=root.findtext("timestamp"),
        username=root.findtext("user"),
        source_ip=root.findtext("src_ip"),
        destination_ip=root.findtext("dst_ip"),
        action=root.findtext("action"),
        status=root.findtext("status"),
        raw_data=log
    )