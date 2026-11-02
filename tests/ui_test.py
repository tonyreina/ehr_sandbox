"""Browser test of the dashboard's Chart / Ask AI tabs (run: pixi run -e dev ui-test [--screenshots DIR] [--dark]).

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
            page = browser.new_page(viewport={"width": 1280, "height": 900}, color_scheme="dark" if "--dark" in sys.argv else "light")
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            asked: list[dict] = []
            answer = {"text": "MOCK ANSWER: Metformin (Medications)."}

            def fake_ask(route):
                asked.append(json.loads(route.request.post_data))
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps({"answer": answer["text"], "model": "gpt-5.3-codex",
                                               "input_tokens": 1234, "output_tokens": 56, "cost_usd": 0.002944,
                                               "cost_estimated": True}))
            page.route("**/api/ask", fake_ask)
            referrals: list[dict] = []

            def fake_referral(route):
                referrals.append(json.loads(route.request.post_data))
                if referrals[-1].get("reason") == "trigger python error":
                    return route.fulfill(status=502, content_type="application/json",
                                         body=json.dumps({"error": "The Python step failed: KeyError: 'missing'"}))
                route.fulfill(status=200, content_type="application/json", body=json.dumps({
                    "letter": "## Referral\n\n**Patient:** Robert Kline\n\n- first point\n- second point\n\nMOCK REFERRAL LETTER", "model": "gpt-5.3-codex", "input_tokens": 400,
                    "output_tokens": 120, "cost_usd": 0.00238, "cost_estimated": True,
                    "sees": {"system": "You are an assistant helping a clinician draft a referral letter.", "user": "CHART:\nPatient: Maria Alvarez"}}))
            page.route("**/api/referral", fake_referral)

            page.goto(f"http://localhost:{port}/index.html?ehr=hapi")
            page.wait_for_selector("#dash:not([hidden])", timeout=30000)
            page.select_option("#patient-select", "scn-maria")
            page.wait_for_function(
                "() => !document.querySelector('#name').textContent.includes('Alvarez') ? false :"
                " ['meds','labs','allergies','encounters','conditions'].every(id => !/Loading/.test(document.getElementById(id).innerText))"
                " && document.getElementById('meds').innerText.includes('Metformin')", timeout=30000)

            sel = lambda: page.evaluate("['tab-chart','tab-ask'].map(i => document.getElementById(i).getAttribute('aria-selected'))")
            hidden = lambda: page.evaluate("[document.getElementById('pane-chart').hidden, document.getElementById('pane-ask').hidden]")
            green = lambda sel: page.evaluate("(s) => { const c = getComputedStyle(document.querySelector(s)).color.match(/\\d+/g).map(Number); return c[1] > c[0] + 30 && c[1] > c[2] + 30; }", sel)
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
            chips = page.locator("#ask-meta .chip").all_text_contents()
            check("chips show model, estimated cost and token counts",
                  chips == ["Model: gpt-5.3-codex", "Cost: ≈ $0.0029", "Input tokens: 1,234", "Output tokens: 56"])
            check("the cost chip explains it is an estimate", "Estimated" in (page.get_attribute("#ask-meta .chip >> nth=1", "title") or ""))
            check("the request carried the chart and question", len(asked) == 1 and "Metformin" in asked[0]["chart"] and "Summarize" in asked[0]["question"])

            # --- markdown in the answer ---
            md = page.evaluate("""() => parseMarkdown("## Summary\\n\\n- **Metformin** 500 mg\\n- _Lisinopril_\\n\\n| a | b |\\n| - | - |\\n| 1 | 2 |").map(b => b.type)""")
            check("the markdown parser finds headings, lists and tables", md == ["heading", "ul", "table"])
            answer["text"] = "## Summary\n\n- **Metformin** 500 mg\n- *Lisinopril* 10 mg\n\nDear Colleague,\nThanks."
            page.click("#ask-btn")
            page.wait_for_function("() => document.querySelector('#ask-answer h4')")
            check("the answer is shown formatted: heading, bullets, bold and italic, line break",
                  page.locator("#ask-answer h4").text_content() == "Summary" and page.locator("#ask-answer li").count() == 2
                  and page.locator("#ask-answer li strong").text_content() == "Metformin" and page.locator("#ask-answer li em").count() == 1
                  and page.locator("#ask-answer br").count() == 1)
            check("the raw markdown marks are not shown when formatted", "##" not in page.text_content("#ask-answer") and "**" not in page.text_content("#ask-answer"))
            page.click("#ask-plain")
            check("Show plain text shows the markdown as written", "## Summary" in page.text_content("#ask-answer") and "**Metformin**" in page.text_content("#ask-answer")
                  and page.text_content("#ask-plain") == "Show formatted")
            page.click("#ask-plain")
            check("Show formatted goes back", page.locator("#ask-answer li").count() == 2)
            answer["text"] = '<img src=x onerror="window.__xss=1"><script>window.__xss=2</script> **safe** [click](javascript:window.__xss=3)'
            page.click("#ask-btn")
            page.wait_for_function("() => document.querySelector('#ask-answer strong')")
            check("HTML in an answer is shown as text and never runs",
                  page.locator("#ask-answer img, #ask-answer script, #ask-answer a").count() == 0 and "<img" in page.text_content("#ask-answer")
                  and page.evaluate("typeof window.__xss") == "undefined")
            answer["text"] = "MOCK ANSWER: Metformin (Medications)."

            page.click("#sec-ask details summary")
            seen = page.text_content("#ask-chart")
            check("What the AI sees shows the system message", "SYSTEM MESSAGE" in seen and "Not documented in this chart" in seen)
            check("What the AI sees shows the chart and question", "USER MESSAGE" in seen and "== Medications ==" in seen and "QUESTION: Summarize" in seen)
            check("the system message is green", green("#ask-chart .ask-system"))
            check("the system message span holds only the system message",
                  page.text_content("#ask-chart .ask-system").startswith("SYSTEM MESSAGE") and "USER MESSAGE" not in page.text_content("#ask-chart .ask-system"))
            check("the user message is not green", not page.evaluate("() => { const c = getComputedStyle(document.querySelector('#ask-chart')).color.match(/\\d+/g).map(Number); return c[1] > c[0] + 30 && c[1] > c[2] + 30; }"))
            page.fill("#ask-q", "Typed live?")
            check("What the AI sees updates as you type", "QUESTION: Typed live?" in page.text_content("#ask-chart"))

            if "--screenshots" in sys.argv:         # the open "What the AI sees" box
                shots = Path(sys.argv[sys.argv.index("--screenshots") + 1])
                shots.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(shots / "sees.png"), full_page=True)
            page.focus("#tab-ask")
            page.keyboard.press("ArrowLeft")
            check("ArrowLeft moves to the Chart tab", sel() == ["true", "false"])
            page.keyboard.press("ArrowRight")
            check("ArrowRight moves back to Ask AI", sel() == ["false", "true"])

            # --- what the AI is given is fuller than what the screen shows ---
            page.evaluate("""() => renderList("meds", Array.from({length: 12}, (_, i) => [`Med${String(i + 1).padStart(2, "0")}x`, "1 tab", "active"]),
                                              ["Medication", "Dose", "Status"], "No medications on file.", "medications")""")
            shown, ai = page.inner_text("#meds"), page.evaluate("chartText()")
            check("the screen still cuts long lists at 10 rows", "Med10x" in shown and "Med11x" not in shown and "and 2 more" in shown)
            check("the AI gets all 12 medications", all(f"Med{i:02d}x\t" in ai for i in range(1, 13)) and "and 2 more" not in ai)
            page.evaluate("""() => renderList("meds", Array.from({length: 60}, (_, i) => [`Med${String(i + 1).padStart(2, "0")}x`, "", ""]),
                                              ["Medication", "Dose", "Status"], "", "medications")""")
            ai = page.evaluate("chartText()")
            check("very long lists are capped for the AI, and it is told", "Med50x\t" in ai and "Med51x\t" not in ai and "[showing 50 of 60 medications]" in ai)

            page.select_option("#patient-select", "scn-robert")
            page.wait_for_function("() => document.querySelector('#name').textContent.includes('Kline') && !/Loading/.test(document.getElementById('labs').innerText)", timeout=30000)
            ai = page.evaluate("chartText()")
            creat = next((l for l in ai.split("\n") if l.startswith("Creatinine")), "")
            check("the AI gets each lab's history, not just the latest value", creat.count(";") == 4 and ": 1;" in creat and ": 2.6" in creat)

            # --- Referral tab ---
            page.click("#tab-referral")
            visits = page.locator("#ref-encounter option").all_text_contents()
            check("the Referral tab lists the patient's visits", len(visits) >= 1 and any("Heart failure follow-up" in v for v in visits))
            check("it warns when the dashboard is not on the local practice server", "another server" in page.text_content("#ref-unavailable"))
            page.fill("#ref-reason", "trigger python error")
            page.click("#ref-btn")
            page.wait_for_selector("#ref-status.error")
            check("an error in the Python step is shown, not hidden", "Python step failed: KeyError" in page.text_content("#ref-status") and page.is_hidden("#ref-letter"))
            referrals.clear()
            page.select_option("#ref-specialty", "Endocrinology")
            page.select_option("#ref-urgency", "Urgent")
            page.fill("#ref-reason", "Overdue diabetes review")
            page.click("#ref-btn")
            page.wait_for_selector("#ref-letter:not([hidden])")
            check("the draft letter appears in an editable box", "MOCK REFERRAL LETTER" in page.input_value("#ref-letter"))
            check("the letter has a formatted preview", page.locator("#ref-preview h4").text_content() == "Referral" and page.locator("#ref-preview strong").text_content() == "Patient:"
                  and page.locator("#ref-preview li").count() == 2 and page.is_visible("#ref-preview-label"))
            sent = referrals[0] if referrals else {}
            check("the request names patient, visit, specialty, urgency and reason",
                  sent.get("patientId") == "scn-robert" and sent.get("encounterId", "").startswith("scn-robert-") and
                  (sent.get("specialty"), sent.get("urgency"), sent.get("reason")) == ("Endocrinology", "Urgent", "Overdue diabetes review"))
            check("chips show model, estimated cost and tokens",
                  page.locator("#ref-meta .chip").all_text_contents() == ["Model: gpt-5.3-codex", "Cost: ≈ $0.0024", "Input tokens: 400", "Output tokens: 120"])
            page.click("#sec-referral details summary")
            check("What the AI sees shows the system message in green and the user message",
                  "SYSTEM MESSAGE" in page.text_content("#ref-sees") and "USER MESSAGE" in page.text_content("#ref-sees") and green("#ref-sees .ask-system"))
            page.fill("#ref-letter", "Edited by the clinician")
            check("the letter can be edited", page.input_value("#ref-letter") == "Edited by the clinician")
            check("the preview updates as the letter is edited", page.locator("#ref-preview").text_content().strip() == "Edited by the clinician")
            page.fill("#ref-letter", "## Plan\n\n1. one\n2. two")
            check("an edit with a list and heading shows as a list and heading", page.locator("#ref-preview h4").text_content() == "Plan" and page.locator("#ref-preview ol li").count() == 2)

            page.click("#tab-ask")

            page.select_option("#patient-select", "scn-alex")
            page.wait_for_function("() => document.querySelector('#name').textContent.includes('Rivera')", timeout=30000)
            check("changing patient keeps the tab and clears the old answer", sel() == ["false", "true"] and page.is_hidden("#ask-answer"))
            alex = page.evaluate("chartText()")
            check("an empty allergy list reads 'None documented.' to the AI, without the on-screen help text",
                  "== Allergies ==\nNone documented." in alex and "never recorded" not in alex)
            check("empty medications read 'None documented.' to the AI, not 'on file'", "== Medications ==\nNone documented." in alex and "on file" not in alex)
            check("changing patient hides the old chips", page.is_hidden("#ask-meta"))
            check("changing patient clears the referral draft", page.is_hidden("#ref-letter") and page.is_hidden("#ref-meta") and page.is_hidden("#ref-preview"))
            check("changing patient closes What the AI sees", not page.evaluate("document.querySelector('#sec-ask details').open"))

            page.wait_for_function("() => !/Loading/.test(document.getElementById('allergies').innerText)", timeout=30000)
            check("empty allergy list says 'documented', not 'known'",
                  page.text_content("#chip-allergies") == "No allergies documented"
                  and "None documented" in page.inner_text("#allergies") and "known" not in page.inner_text("#allergies").lower())

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
