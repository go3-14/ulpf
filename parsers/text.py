def parse_text(raw_log: str) -> dict | None:
    value = raw_log.rstrip("\r\n")
    return {"message": value} if value else None
