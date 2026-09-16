import time

from ingest.pipeline import process


SAMPLE = b"<166>Jan 10 10:00:00 asa-fw %ASA-6-302013: Built outbound TCP connection 1 for src outside:192.0.2.10/54321 dst inside:198.51.100.20/443\n"


def main(count=10000):
    start = time.perf_counter()
    ok = 0
    for _ in range(count):
        if process(SAMPLE):
            ok += 1
    elapsed = time.perf_counter() - start
    print({"events": ok, "seconds": elapsed, "events_per_second": ok / elapsed if elapsed else 0})


if __name__ == "__main__":
    main()
