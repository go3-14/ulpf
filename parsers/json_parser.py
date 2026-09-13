import json
from normalisation.event import NormalizedEvent


def parse(log):

    data = json.loads(log)

    return NormalizedEvent(
        event_type=data.get("event"),
        timestamp=data.get("timestamp"),
        username=data.get("user"),
        source_ip=data.get("src_ip"),
        destination_ip=data.get("dst_ip"),
        action=data.get("action"),
        status=data.get("status"),
        raw_data=data
    )