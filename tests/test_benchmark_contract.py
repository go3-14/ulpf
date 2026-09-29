from scripts.benchmark import run_once

def test_benchmark_exposes_single_run_function():
    assert callable(run_once)
