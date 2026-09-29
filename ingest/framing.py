import re

class LineJoiner:
    def __init__(self, start: str, max_lines: int = 200, max_bytes: int = 1048576):
        self.pattern = re.compile(start)
        self.max_lines = max_lines; self.max_bytes = max_bytes
        self._lines = []; self._size = 0

    def push(self, line: bytes):
        text = line.decode("utf-8", errors="replace")
        flushed = []
        if self._lines and self.pattern.search(text): flushed.append(b"\n".join(self._lines)); self._lines=[]; self._size=0
        if not self._lines and not self.pattern.search(text): flushed.append(line); return flushed
        self._lines.append(line); self._size += len(line)
        if len(self._lines) >= self.max_lines or self._size >= self.max_bytes:
            flushed.append(b"\n".join(self._lines)); self._lines=[]; self._size=0
        return flushed

    def flush(self):
        if not self._lines: return []
        result = [b"\n".join(self._lines)]; self._lines=[]; self._size=0; return result
