"""Browser test of the dashboard's Chart / Ask AI tabs (run: pixi run -e dev ui-test [--screenshots DIR]).

Needs no internet and no token: the dashboard talks to a small fake FHIR server built from the
teaching scenarios in ehr/scenarios.py, and the /api/ask call is answered by the test.
Install the browser once with: pixi run -e dev install-browser
"""
import json
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ehr import scenarios  # noqa: E402


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def fake_fhir(resources: list[dict]) -> ThreadingHTTPServer:
    """A read-only FHIR server over *resources* (search by patient, _id, name and category)."""
    def category(r: dict) -> set[str]:
        return {c["code"] for cat in r.get("category", []) for c in cat.get("coding", [])}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, body: dict, status: int = 200):
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/fhir+json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.end_headers()

        def do_GET(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            parts = [p for p in u.path.split("/") if p]
            if parts == ["metadata"]:
                return self._send({"resourceType": "CapabilityStatement", "fhirVersion": "4.0.1"})
            rtype = parts[0] if parts else ""
            found = [r for r in resources if r["resourceType"] == rtype]
            if len(parts) == 2:
                hit = [r for r in found if r["id"] == parts[1]]
                return self._send(hit[0] if hit else {"resourceType": "OperationOutcome"}, 200 if hit else 404)
            pid = (q.get("patient") or q.get("subject") or "").split("/")[-1]
            if pid:
                found = [r for r in found if pid in json.dumps(r.get("subject") or r.get("patient") or {})]
            if "_id" in q:
                found = [r for r in found if r["id"] in q["_id"].split(",")]
            if q.get("name"):
                found = [r for r in found if q["name"].lower() in json.dumps(r.get("name", [])).lower()]
            if q.get("category"):
                want = q["category"].split("|")[-1]
                found = [r for r in found if want in category(r)]
            self._send({"resourceType": "Bundle", "type": "searchset", "total": len(found),
                        "entry": [{"resource": r} for r in found]})

    return ThreadingHTTPServer(("127.0.0.1", free_port()), H)


def main() -> None:
    resources = [e["resource"] for key in scenarios.SCENARIOS for e in scenarios.bundle(key)["entry"]]
    fhir = fake_fhir(resources)
    threading.Thread(target=fhir.serve_forever, daemon=True).start()
    port = free_port()
    code = (f"import cli; cli.SMART_PORT={port}; cli.SMART_BASE='http://localhost:{port}'; "
            "cli.smart_app(ehr='hapi', open_browser=False, console=False, keep_hapi=True)")
    env = {k: v for k, v in __import__("os").environ.items() if k != "OPENAI_TOKEN"}
    env["HAPI_FHIR_BASE"] = f"http://127.0.0.1:{fhir.server_port}"       # keeps smart-app off Docker
    server = subprocess.Popen([sys.executable, "-c", code], cwd=ROOT, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    failures: list[str] = []

    def check(label: str, ok: bool) -> None:
        print(("PASS  " if ok else "FAIL  ") + label)
        if not ok:
            failures.append(label)

    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://localhost:{port}/__ehr.js", timeout=1)
                break
            except OSError:
                time.sleep(0.5)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            asked: list[dict] = []

            def fake_ask(route):
                asked.append(json.loads(route.request.post_data))
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps({"answer": "MOCK ANSWER: Metformin (Medications)."}))
            page.route("**/api/ask", fake_ask)

            page.goto(f"http://localhost:{port}/index.html?ehr=hapi")
            page.wait_for_selector("#dash:not([hidden])", timeout=30000)
            page.select_option("#patient-select", "scn-maria")
            page.wait_for_function(
                "() => !document.querySelector('#name').textContent.includes('Alvarez') ? false :"
                " ['meds','labs','allergies','encounters','conditions'].every(id => !/Loading/.test(document.getElementById(id).innerText))"
                " && document.getElementById('meds').innerText.includes('Metformin')", timeout=30000)

            sel = lambda: page.evaluate("['tab-chart','tab-ask'].map(i => document.getElementById(i).getAttribute('aria-selected'))")
            hidden = lambda: page.evaluate("[document.getElementById('pane-chart').hidden, document.getElementById('pane-ask').hidden]")
            check("starts on the Chart tab", sel() == ["true", "false"] and hidden() == [False, True])
            check("sidebar no longer has an Ask link", page.locator('.sidebar a[href="#sec-ask"]').count() == 0)

            on_chart = page.evaluate("chartText()")
            page.click("#tab-ask")
            check("clicking Ask AI shows the Ask pane and hides the chart", sel() == ["false", "true"] and hidden() == [True, False])
            on_ask = page.evaluate("chartText()")
            check("chart text is identical whichever tab is showing", on_chart == on_ask)
            check("chart text keeps its line structure and content", on_ask.count("\n") > 15 and "Metformin" in on_ask)
            check("reading the chart leaves the chart pane hidden", hidden() == [True, False])

            page.click("#ask-examples button >> nth=0")
            page.click("#ask-btn")
            page.wait_for_selector("#ask-answer:not([hidden])")
            check("the mocked answer is shown", "MOCK ANSWER" in page.text_content("#ask-answer"))
            check("the request carried the chart and question", len(asked) == 1 and "Metformin" in asked[0]["chart"] and "Summarize" in asked[0]["question"])

            page.click("#sec-ask details summary")
            seen = page.text_content("#ask-chart")
            check("What the AI sees shows the system message", "SYSTEM MESSAGE" in seen and "Not documented in this chart" in seen)
            check("What the AI sees shows the chart and question", "USER MESSAGE" in seen and "== Medications ==" in seen and "QUESTION: Summarize" in seen)
            page.fill("#ask-q", "Typed live?")
            check("What the AI sees updates as you type", "QUESTION: Typed live?" in page.text_content("#ask-chart"))

            page.focus("#tab-ask")
            page.keyboard.press("ArrowLeft")
            check("ArrowLeft moves to the Chart tab", sel() == ["true", "false"])
            page.keyboard.press("ArrowRight")
            check("ArrowRight moves back to Ask AI", sel() == ["false", "true"])

            page.select_option("#patient-select", "scn-alex")
            page.wait_for_function("() => document.querySelector('#name').textContent.includes('Rivera')", timeout=30000)
            check("changing patient keeps the tab and clears the old answer", sel() == ["false", "true"] and page.is_hidden("#ask-answer"))
            check("changing patient closes What the AI sees", not page.evaluate("document.querySelector('#sec-ask details').open"))

            check("no JavaScript errors", not errors)
            if errors:
                print("      ", errors[:3])
            if "--screenshots" in sys.argv:         # --screenshots DIR saves both tabs
                out = Path(sys.argv[sys.argv.index("--screenshots") + 1])
                out.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(out / "ask.png"), full_page=True)
                page.click("#tab-chart")
                page.screenshot(path=str(out / "chart.png"), full_page=True)
            browser.close()
    finally:
        server.terminate()
        fhir.shutdown()
    if failures:
        sys.exit(f"{len(failures)} check(s) failed")
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
