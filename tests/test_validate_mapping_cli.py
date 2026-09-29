def test_validate_mapping_command_is_registered():
    from cli.main import main
    import cli.main as module
    assert callable(module.cmd_validate_mapping)
