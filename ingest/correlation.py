from collections import defaultdict

def correlate(events, key="src_ip", window=300, min_sources=2):
    groups = defaultdict(list)
    for event in events:
        value = event.get(key) or event.get("src_endpoint", {}).get("ip")
        if value is None: continue
        bucket = int(event.get("time", 0) // (window * 1000))
        groups[(value, bucket)].append(event)
    result = []
    for (value, bucket), items in groups.items():
        sources = sorted({next((x.split(":", 1)[1] for x in event.get("metadata", {}).get("labels", []) if x.startswith("source:")), "") for event in items})
        if len([x for x in sources if x]) >= min_sources:
            result.append({"key": value, "sources": sources, "event_ids": [event.get("metadata", {}).get("uid") for event in items]})
    return result
