from scripts.make_demo_scenario import generate

def test_demo_scenario_is_deterministic(tmp_path):
    first = generate(tmp_path / "a", 1)
    second = generate(tmp_path / "b", 1)
    assert (first / "sshd_synthetic.log").read_bytes() == (second / "sshd_synthetic.log").read_bytes()
