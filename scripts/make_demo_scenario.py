import argparse
import json
import random
from pathlib import Path

def generate(output="demo", seed=1):
    rng = random.Random(seed); out = Path(output); out.mkdir(parents=True, exist_ok=True)
    attacker = "203.0.113.50"
    lines = [json.dumps({"src_ip": attacker, "dst_port": 22, "action": "deny", "seq": i}) for i in range(5)]
    (out / "firewall_synthetic.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    ssh = [f"<34>Sep 29 10:15:{10+i:02d} host sshd: Failed password for invalid user bob from {attacker} port {2200+i}" for i in range(3)]
    (out / "sshd_synthetic.log").write_text("\n".join(ssh) + "\n", encoding="utf-8")
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--seed", type=int, default=1); parser.add_argument("--out", default="demo")
    args = parser.parse_args(); print(generate(args.out, args.seed))
