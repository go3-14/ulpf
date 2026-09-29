"""Durable SQLite event index."""
import pathlib, sqlite3, threading
import config

_index_map = {}
_index_lock = threading.RLock()
_index_loaded = False

def _db_path(): return pathlib.Path(config.STORAGE_DIR) / "index" / "index.sqlite3"

def _connect():
    p = _db_path(); p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(p, timeout=5); c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA synchronous=NORMAL"); c.execute("PRAGMA busy_timeout=5000")
    c.execute("""CREATE TABLE IF NOT EXISTS events (
      event_id TEXT PRIMARY KEY, kind TEXT NOT NULL DEFAULT 'event', source_id TEXT, format TEXT, class_uid INTEGER,
      time_ms INTEGER, received_ms INTEGER NOT NULL DEFAULT 0, fallback INTEGER NOT NULL DEFAULT 0,
      src_ip TEXT, dst_ip TEXT, src_port INTEGER, dst_port INTEGER, user_name TEXT,
      origin TEXT, origin_id TEXT, origin_offset INTEGER, origin_line INTEGER,
      mapping_id TEXT, mapping_version TEXT, mapping_sha256 TEXT,
      raw_file TEXT NOT NULL, raw_offset INTEGER NOT NULL, raw_length INTEGER NOT NULL, raw_sha256 TEXT NOT NULL,
      norm_file TEXT, norm_offset INTEGER, norm_length INTEGER)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON events(time_ms)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_origin ON events(origin, origin_id)")
    c.execute("PRAGMA user_version=1"); c.commit(); return c

def _ensure_loaded():
    global _index_loaded
    if _index_loaded: return
    with _index_lock:
        if _index_loaded: return
        _index_map.clear()
        with _connect() as c:
            for r in c.execute("SELECT event_id,raw_file,raw_offset,raw_length FROM events"):
                _index_map[r["event_id"]] = (str(pathlib.Path(config.STORAGE_DIR) / r["raw_file"]), r["raw_offset"], r["raw_length"])
        _index_loaded = True

def _relative(path):
    p = pathlib.Path(path)
    try: return str(p.resolve().relative_to(pathlib.Path(config.STORAGE_DIR).resolve())).replace("\\", "/")
    except ValueError: return str(p).replace("\\", "/")

def add_index(event_id, path, offset, length, **metadata):
    _ensure_loaded(); vals = {
      "event_id":event_id,"raw_file":_relative(path),"raw_offset":offset,"raw_length":length,
      "raw_sha256":metadata.get("raw_sha256", ""),"origin":metadata.get("origin"),"origin_id":metadata.get("origin_id"),
      "origin_offset":metadata.get("origin_offset"),"origin_line":metadata.get("origin_line"),"received_ms":metadata.get("received_ms",0),
      "source_id":metadata.get("source_id"),"format":metadata.get("format"),"class_uid":metadata.get("class_uid"),"time_ms":metadata.get("time_ms"),
      "fallback":int(bool(metadata.get("fallback",False))),"mapping_id":metadata.get("mapping_id"),"mapping_version":metadata.get("mapping_version"),
      "mapping_sha256":metadata.get("mapping_sha256"),"norm_file":metadata.get("norm_file"),"norm_offset":metadata.get("norm_offset"),"norm_length":metadata.get("norm_length")}
    with _index_lock, _connect() as c:
        cur = c.execute("""INSERT OR IGNORE INTO events
          (event_id,raw_file,raw_offset,raw_length,raw_sha256,origin,origin_id,origin_offset,origin_line,received_ms,source_id,format,class_uid,time_ms,fallback,mapping_id,mapping_version,mapping_sha256,norm_file,norm_offset,norm_length)
          VALUES (:event_id,:raw_file,:raw_offset,:raw_length,:raw_sha256,:origin,:origin_id,:origin_offset,:origin_line,:received_ms,:source_id,:format,:class_uid,:time_ms,:fallback,:mapping_id,:mapping_version,:mapping_sha256,:norm_file,:norm_offset,:norm_length)""", vals)
        inserted = cur.rowcount == 1; c.commit()
        if inserted: _index_map[event_id] = (str(pathlib.Path(config.STORAGE_DIR)/vals["raw_file"]), offset, length)
        return inserted

def get_index(event_id):
    _ensure_loaded()
    with _index_lock: return _index_map.get(event_id)

def get_record(event_id):
    with _index_lock, _connect() as c:
        r = c.execute("SELECT * FROM events WHERE event_id=?", (event_id,)).fetchone()
        return dict(r) if r else None

def search_records(**filters):
    clauses=[]; params=[]
    for key in ("source_id","origin","origin_id","format"):
        if filters.get(key) is not None: clauses.append(key+"=?"); params.append(filters[key])
    sql="SELECT * FROM events"+(" WHERE "+" AND ".join(clauses) if clauses else "")
    with _connect() as c: return [dict(r) for r in c.execute(sql, params)]
