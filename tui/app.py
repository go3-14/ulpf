"""Single-screen live ULPF demo harness over the real FastAPI service."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path

import httpx
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Header, RichLog, Static, TextArea

API_URL = os.environ.get("ULPF_DEMO_API", "http://127.0.0.1:8000")
ROOT = Path(__file__).resolve().parents[1]
# Textual owns the terminal. HTTP polling must not print a request line above
# the app on every refresh.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
CHECKS = {
    "formats": "Multi-format parse",
    "resilience": "Crash-resilience",
    "replay": "Failed/replay recovery",
    "onboarding": "New source onboard",
    "traceability": "Traceability check",
    "classes": "Class-aware routing",
}

class DemoApp(App):
    TITLE = "ULPF Live Check"
    CSS = """
    Screen { background: $surface; }
    #main { height: 1fr; padding: 1; }
    #top { height: 9; min-height: 9; }
    .panel { border: round $primary; padding: 1; margin-right: 1; height: 100%; }
    #metrics { width: 42%; }
    #checks { width: 58%; }
    #sample { height: 3; min-height: 3; border: round $accent; }
    #actions { height: 5; min-height: 5; padding: 1 0; }
    #actions Button { width: 1fr; min-width: 16; margin-right: 1; }
    #log { height: 1fr; border: round $secondary; }
    """
    BINDINGS = [("r", "refresh", "Refresh"), ("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main"):
            with Horizontal(id="top"):
                yield Static("METRICS\nConnecting…", id="metrics", classes="panel", markup=False)
                yield Static(self.check_text(), id="checks", classes="panel", markup=False)
            yield TextArea(
                '{"timestamp":"2026-01-10T10:00:00Z","src_ip":"192.0.2.1","dst_ip":"198.51.100.2","action":"allow"}',
                id="sample",
            )
            with Horizontal(id="actions"):
                yield Button("Run Onboarding Test", id="onboarding")
                yield Button("Run Resilience Test", id="resilience")
                yield Button("Run Replay Test", id="replay")
                yield Button("Show Random Raw↔OCSF", id="traceability")
                yield Button("Run Coverage Sweep", id="coverage")
                yield Button("Show Scale Numbers", id="scale")
            yield RichLog(id="log", highlight=True, markup=False)
        yield Footer()

    def check_text(self) -> str:
        values = getattr(self, "check_state", {key: "..." for key in CHECKS})
        return "\n".join(["CHECKLIST"] + [f"[{values[key]:^7}] {label}" for key, label in CHECKS.items()])

    async def on_mount(self) -> None:
        self.check_state = {key: "..." for key in CHECKS}
        self.set_interval(1, self.poll_service)
        await self.poll_service()
        self.write_log("Harness ready — every action calls the real ULPF service.")

    async def api(self, method: str, path: str, **kwargs):
        try:
            async with httpx.AsyncClient(base_url=API_URL, timeout=10) as client:
                response = await client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            return {"error": str(exc)}

    def write_log(self, message: str) -> None:
        self.query_one("#log", RichLog).write(f"{time.strftime('%H:%M:%S')}  {message}")

    def set_check(self, key: str, state: str) -> None:
        self.check_state[key] = state
        self.query_one("#checks", Static).update(self.check_text())

    async def poll_service(self) -> None:
        metrics = await self.api("GET", "/metrics")
        health = await self.api("GET", "/health")
        status = "● healthy" if "error" not in health else "● OFFLINE"
        processed = metrics.get("processed_total", 0)
        failed = metrics.get("failed_total", 0)
        elapsed = max(float(metrics.get("uptime_seconds", 0)), 1.0)
        self.query_one("#metrics", Static).update(
            f"METRICS                         {status}\n"
            f"Ingested:     {processed:>8}\nNormalized:   {processed:>8}\n"
            f"Failed:       {failed:>8}\nEvents/sec:   {processed / elapsed:>8.1f}\n"
            f"Sources live: {len(metrics.get('processed_by_source', {})):>8}"
        )

    async def action_refresh(self) -> None:
        await self.poll_service()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        action = event.button.id
        if action in self.check_state:
            self.set_check(action, "RUNNING")
        try:
            handlers = {"coverage": self.run_coverage, "onboarding": self.run_onboarding,
                        "replay": self.run_replay, "resilience": self.run_resilience,
                        "traceability": self.run_traceability, "scale": self.run_scale}
            await handlers[action]()
        except Exception as exc:
            self.write_log(f"FAIL {action}: {exc}")
            if action in self.check_state: self.set_check(action, "FAIL")

    async def run_coverage(self) -> None:
        names = ["cisco_asa_syslog.log", "paloalto_cef.log", "generic_leef.log",
                 "generic_json.log", "generic_xml.log", "generic_csv.log", "dns_json.log"]
        classes, passed = set(), 0
        for name in names:
            content = (ROOT / "samples" / name).read_text(encoding="utf-8")
            result = await self.api("POST", "/ingest", json={"logs": [content]})
            ids = result.get("event_ids", [])
            if ids:
                event = await self.api("GET", f"/events/{ids[-1]}")
                classes.add(event.get("class_uid")); passed += 1
                self.write_log(f"coverage {name}: PASS → class={event.get('class_uid')}")
            else:
                self.write_log(f"coverage {name}: FAIL → {result}")
        self.set_check("formats", "PASS" if passed == len(names) else "FAIL")
        self.set_check("classes", "PASS" if len(classes) >= 2 else "FAIL")
        self.write_log(f"coverage complete: {passed}/{len(names)} sources, classes={sorted(classes)}")

    async def run_onboarding(self) -> None:
        started = time.perf_counter()
        sample = self.query_one("#sample", TextArea).text
        source = f"demo_source_{int(time.time())}"
        suggestion = await self.api("POST", "/onboarding/suggest", json={"sample": sample, "source": source})
        tested = await self.api("POST", "/onboarding/test", json={"sample": sample, "mapping": suggestion})
        saved = await self.api("POST", "/onboarding/save", json={"mapping": suggestion})
        ingested = await self.api("POST", "/ingest", json={"logs": sample})
        elapsed = time.perf_counter() - started
        ok = tested.get("valid") and saved.get("mappings_count") and ingested.get("event_ids")
        self.write_log(f"onboarding: suggest → test → save/reload → ingest in {elapsed:.2f}s")
        self.set_check("onboarding", "PASS" if ok else "FAIL")

    async def run_replay(self) -> None:
        failed = await self.api("GET", "/failed")
        if not isinstance(failed, list) or not failed:
            self.write_log("replay: no existing failed event to recover; paste an unmapped source first")
            self.set_check("replay", "...")
            return
        result = await self.api("POST", "/replay", params={"limit": 25})
        self.write_log(f"replay test: failed-store entries={len(failed) if isinstance(failed, list) else 0}, result={result}")
        self.set_check("replay", "PASS" if result.get("recovered", 0) > 0 else "FAIL")

    async def run_resilience(self) -> None:
        spool = ROOT / "spool"; spool.mkdir(exist_ok=True)
        path = spool / f"demo-{int(time.time())}.log"
        path.write_bytes(b'{"timestamp":"2026-01-10T10:00:00Z","action":"allow"}\n')
        self.write_log("resilience: dropped a spool event; watcher checkpoint path exercised")
        self.write_log("resilience: restart verification is not automatic yet, so this remains pending")
        self.set_check("resilience", "...")

    async def run_traceability(self) -> None:
        events = await self.api("GET", "/events", params={"limit": 1})
        if not events:
            self.write_log("traceability: no events available; run coverage first")
            self.set_check("traceability", "FAIL"); return
        event = events[0]; eid = event.get("metadata", {}).get("uid")
        raw = await self.api("GET", f"/events/{eid}/raw")
        self.write_log(json.dumps({"raw": raw, "mapping_version": event.get("mapping_version"), "ocsf": event}, indent=2))
        self.set_check("traceability", "PASS" if eid and "mapping_version" in event else "FAIL")

    async def run_scale(self) -> None:
        proc = await asyncio.create_subprocess_exec(os.environ.get("PYTHON", "python"), str(ROOT / "scripts" / "benchmark.py"),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, cwd=ROOT)
        output, _ = await proc.communicate()
        self.write_log(output.decode(errors="replace"))
        self.write_log("projection: 1B/day requires ~11,574 events/sec; divide by measured events/sec/core")

if __name__ == "__main__":
    DemoApp().run()
