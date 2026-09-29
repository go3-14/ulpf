from pathlib import Path

def test_offline_bundle_scripts_exist():
    assert Path("scripts/build_offline_bundle.sh").exists()
    assert Path("scripts/build_offline_bundle.ps1").exists()
