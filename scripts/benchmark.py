import os
import pathlib
import sys
import time
import statistics

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.resolve()))
from ingest.pipeline import process


SAMPLE_SYSLOG = b"<134>Jan 10 10:00:00 fw01 %ASA-6-302013: Built inbound TCP connection 12345 for outside:192.168.1.50/49152 to inside:10.0.0.5/80"
SAMPLE_CEF = b"<134>Jan 10 10:00:00 PA-FW CEF:0|Palo Alto Networks|PAN-OS|10.1.0|TRAFFIC|end|1|rt=Jan 10 2026 10:00:00 src=192.168.1.100 spt=54321 dst=198.51.100.20 dpt=443 proto=tcp action=allow"
SAMPLE_LEEF = b"LEEF:1.0|VendorName|ProductName|1.0|100|devTime=Jan 10 2026 10:00:00 GMT\tsrc=192.168.1.10\tsrcPort=12345\tdst=10.0.0.1\tdstPort=80\tproto=TCP\taction=Built"
SAMPLE_JSON = b'{"timestamp": "2026-01-10T10:00:00Z", "src_ip": "192.168.1.200", "src_port": 60000, "dst_ip": "10.0.0.50", "dst_port": 8080, "protocol": "TCP", "action": "allow", "severity": "info"}'

SAMPLES = [SAMPLE_SYSLOG, SAMPLE_CEF, SAMPLE_LEEF, SAMPLE_JSON]

def run_once(num_events: int):
    t0 = time.perf_counter(); success_count = 0
    for i in range(num_events):
        if process(SAMPLES[i % len(SAMPLES)]): success_count += 1
    elapsed = time.perf_counter() - t0
    return success_count / elapsed if elapsed else 0.0

def run_benchmark(num_events: int = 5000):
    print(f"Starting ULPF benchmark with {num_events} events across 4 formats...")

    rates = [run_once(num_events) for _ in range(3)]
    eps = statistics.median(rates)

    import config
    storage_dir = pathlib.Path(config.STORAGE_DIR)
    total_bytes = sum(f.stat().st_size for f in storage_dir.rglob("*") if f.is_file())

    print("=== BENCHMARK RESULTS ===")
    print(f"Total events submitted: {num_events}")
    print(f"Median of 3 throughput:  {eps:.1f} events/sec")
    print(f"Throughput:             {eps:.1f} events/sec")
    print(f"Storage size on disk:   {total_bytes / (1024*1024):.2f} MB")

if __name__ == "__main__":
    run_benchmark()
