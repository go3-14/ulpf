import csv
import io

def parse_csv(raw_log: str) -> dict | None:
    try:
        rows = list(csv.reader(io.StringIO(raw_log)))
    except csv.Error:
        return None
    if not rows:
        return None
    if len(rows) == 1:
        return {f"field_{i}": v for i, v in enumerate(rows[0])}
    headers, values = rows[0], rows[1]
    result = {h.strip(): values[i].strip() if i < len(values) else "" for i, h in enumerate(headers) if h.strip()}
    for i, value in enumerate(values[len(headers):], len(headers)):
        result[f"col_{i}"] = value.strip()
    return result
