def test_demo_run_entrypoint():
    from scripts.demo_run import main
    assert callable(main)
