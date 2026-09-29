"""Deterministic code-side demo driver."""
from scripts.make_demo_scenario import generate

def main():
    print("1. generate deterministic scenario")
    print(generate("demo", 1))
    print("2. ingest with the service/API")
    print("3. inspect metrics, events, provenance, search, and correlation")
    print("4. run air-gap proof")

if __name__ == "__main__": main()
