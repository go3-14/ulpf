import queue
import threading
from ingest.pipeline import process
from ingest.context import IngestContext

class IngestionQueue:
    """Bounded producer/consumer queue; put() blocks for backpressure."""
    def __init__(self, maxsize=10000, workers=1):
        self.items = queue.Queue(maxsize=maxsize)
        self.stop = threading.Event()
        self.threads = [threading.Thread(target=self._worker, daemon=True) for _ in range(workers)]
    def start(self):
        for t in self.threads: t.start()
        return self
    def put(self, raw, timeout=None, ctx: IngestContext | None = None):
        self.items.put((raw, ctx), timeout=timeout)
    def _worker(self):
        while not self.stop.is_set() or not self.items.empty():
            try: raw, ctx = self.items.get(timeout=.2)
            except queue.Empty: continue
            try: process(raw, ctx=ctx)
            finally: self.items.task_done()
    def close(self):
        self.stop.set()
        self.items.join()
        for t in self.threads: t.join(timeout=2)
