"""Tests for n8n/step_server.py and the Python steps in n8n/steps (run: pixi run steps-test). No Docker needed."""
import json
import os
import shutil
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
tmp = tempfile.mkdtemp()
shutil.copytree(ROOT / "n8n" / "steps", tmp, dirs_exist_ok=True)
os.environ["STEPS_DIR"] = tmp
sys.path.insert(0, str(ROOT / "n8n"))
import step_server  # noqa: E402
from ehr import scenarios  # noqa: E402
from fake_fhir import fake_fhir, free_port  # noqa: E402

REPLY = {"model": "gpt-5.3-codex",
         "output": [{"type": "reasoning", "content": []},
                    {"type": "message", "content": [{"type": "output_text", "text": "  Dear Colleague, "}, {"type": "output_text", "text": "Thanks.\n"}]}],
         "usage": {"input_tokens": 161, "output_tokens": 18, "input_tokens_details": {"cached_tokens": 5}}}


def records(key: str, reason: str | None = None) -> dict:
    """What the workflow sends to build_prompt for a teaching patient: each search result as a FHIR bundle."""
    res = [e["resource"] for e in scenarios.bundle(key)["entry"]]
    of = lambda t, cat=None: {"resourceType": "Bundle", "entry": [{"resource": r} for r in res if r["resourceType"] == t]}
    visits = [r for r in res if r["resourceType"] == "Encounter"]
    visit = next((r for r in visits if reason and r["reasonCode"][0]["text"] == reason), None) or max(visits, key=lambda r: r["period"]["start"])
    return {"request": {"patientId": f"scn-{key}", "encounterId": visit["id"], "specialty": "Endocrinology", "urgency": "Urgent", "reason": "Overdue review"},
            "patient": next(r for r in res if r["resourceType"] == "Patient"), "encounter": visit,
            "problems": of("Condition"), "medications": of("MedicationRequest"), "allergies": of("AllergyIntolerance"), "labs": of("Observation")}


def main() -> None:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), step_server.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    failures = []

    def post(name: str, body) -> tuple[int, dict]:
        req = urllib.request.Request(f"{base}/{name}", data=json.dumps(body).encode(), method="POST", headers={"Content-Type": "application/json"})
        try:
            r = urllib.request.urlopen(req)
            return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def check(label: str, ok: bool) -> None:
        print(("PASS  " if ok else "FAIL  ") + label)
        if not ok:
            failures.append(label)

    status, out = post("pick_letter", REPLY)
    check("pick_letter returns the letter, model and token counts",
          status == 200 and out == {"letter": "Dear Colleague, Thanks.", "model": "gpt-5.3-codex", "input_tokens": 161, "output_tokens": 18, "cached_tokens": 5})
    status, out = post("pick_letter", {})
    check("an empty reply gives an empty letter instead of an error", status == 200 and out["letter"] == "" and out["input_tokens"] is None)
    check("healthz answers", json.load(urllib.request.urlopen(f"{base}/healthz")) == {"ok": True})

    check("an unknown step is a 404 that says what to create", post("nope", {})[0] == 404 and "n8n/steps/nope.py" in post("nope", {})[1]["error"])
    check("a bad step name is refused", post("..%2Fetc", {})[0] == 400 and post("Pick-Letter", {})[0] == 400)

    # Editing the file changes the next answer, without restarting the server.
    path = Path(tmp) / "pick_letter.py"
    path.write_text(path.read_text().replace('.strip()', '.strip().replace("Colleague", "Doctor")'))
    check("a saved edit applies to the next request", post("pick_letter", REPLY)[1]["letter"] == "Dear Doctor, Thanks.")

    path.write_text("def run(reply):\n    return {'letter': reply['missing']}\n")
    status, out = post("pick_letter", REPLY)
    check("an error in the step is a 500 that names the problem", status == 500 and "KeyError" in out["error"])
    path.write_text("def run(reply)\n    return {}\n")
    status, out = post("pick_letter", REPLY)
    check("a typo in the file is a 500 that names the problem", status == 500 and "SyntaxError" in out["error"])
    path.write_text("def run(reply):\n    return {'x': object()}\n")
    check("a result that is not JSON is a 500, not a broken reply", post("pick_letter", REPLY)[0] == 500)

    # --- build_prompt: the words the AI is told and the chart text it reads ---
    status, out = post("build_prompt", records("maria", "Diabetes follow-up"))
    user = out["request"]["input"] if status == 200 else ""
    check("build_prompt writes the chart text from the records",
          all(t in user for t in ("Patient: Maria Alvarez", "Type 2 diabetes mellitus", "Metformin 500 mg tablet - 500 mg by mouth twice daily",
                                  "Hemoglobin A1c: 7.8 %", "Reason: Diabetes follow-up", "Type: Ambulatory visit")))
    check("it adds the clinician's request (specialty, urgency, reason)", all(t in user for t in ("Specialty: Endocrinology", "Urgency: Urgent", "reason for referral: Overdue review")))
    check("the request asks for the default model and tells the proxy not to store the chart",
          out["request"]["model"] == "gpt-5.3-codex" and out["request"]["store"] is False)
    check("the instructions list every heading and the closing line",
          all(h in out["request"]["instructions"] for h in ("Patient", "Reason for referral", "Question for the specialist")) and "Draft for clinician review. Not sent." in out["request"]["instructions"])
    check("what the AI sees is exactly what is sent", out["sees"] == {"system": out["request"]["instructions"], "user": out["request"]["input"]})
    check("a model named by the workflow is used", post("build_prompt", {**records("maria"), "model": "other-model"})[1]["request"]["model"] == "other-model")
    check("a patient with nothing recorded reads 'None documented.'",
          "== Allergies ==\nNone documented." in post("build_prompt", records("alex"))[1]["request"]["input"])
    check("a record that is missing does not break it", post("build_prompt", {})[0] == 200)

    prompt_path = Path(tmp) / "build_prompt.py"
    prompt_path.write_text(prompt_path.read_text().replace('"Urgency",\n]', '"Urgency",\n    "Follow-up plan",\n]'))
    check("a heading added in the file reaches the instructions on the next request",
          "Follow-up plan" in post("build_prompt", records("maria"))[1]["request"]["instructions"])
    prompt_path.write_text(prompt_path.read_text().replace('Keep the letter to one page.', 'Keep the letter to three sentences.'))
    check("a changed rule reaches the instructions", "three sentences" in post("build_prompt", records("maria"))[1]["sees"]["system"])

    # --- pick_letter.format_letter: switch on a line in the file ---
    shutil.copy(ROOT / "n8n" / "steps" / "pick_letter.py", path)
    path.write_text(path.read_text().replace('    # letter = letter.replace("**", "")', '    letter = letter.replace("**", "")'))
    reply = {**REPLY, "output": [{"type": "message", "content": [{"type": "output_text", "text": "**Patient:** Maria"}]}]}
    check("format_letter can clean up the letter once a line is switched on", post("pick_letter", reply)[1]["letter"] == "Patient: Maria")

    # --- get_chart: which records the AI gets to see, read from the practice server ---
    resources = [e["resource"] for k in scenarios.SCENARIOS for e in scenarios.bundle(k)["entry"]]
    fhir = fake_fhir(resources)
    threading.Thread(target=fhir.serve_forever, daemon=True).start()
    os.environ["HAPI_BASE"] = f"http://127.0.0.1:{fhir.server_port}"
    visit = next(r["id"] for r in resources if r["resourceType"] == "Encounter" and r["reasonCode"][0]["text"] == "Diabetes follow-up")
    ask = {"patientId": "scn-maria", "encounterId": visit, "specialty": "Endocrinology", "urgency": "Routine", "reason": "Overdue review"}

    status, chart = post("get_chart", ask)
    check("get_chart reads the patient, the visit and the four lists",
          status == 200 and chart["patient"]["id"] == "scn-maria" and chart["encounter"]["id"] == visit
          and all(chart[k]["resourceType"] == "Bundle" and chart[k]["entry"] for k in ("problems", "medications", "allergies", "labs") if k != "allergies"))
    check("it passes the request along unchanged", chart["request"] == ask)
    paths = " ".join(fhir.seen)
    check("it asks the server for each record with the settings at the top of the file",
          f"/Patient/scn-maria" in paths and f"/Encounter/{visit}" in paths and "Condition?patient=scn-maria&_count=50" in paths
          and "category=laboratory" in paths and "_sort=-date" in paths and "_count=100" in paths)
    status, built = post("build_prompt", chart)
    check("get_chart's answer goes straight into build_prompt",
          status == 200 and "Patient: Maria Alvarez" in built["request"]["input"] and "Hemoglobin A1c: 7.8" in built["request"]["input"]
          and "Reason: Diabetes follow-up" in built["request"]["input"])
    check("build_prompt passes an error on instead of building from nothing", post("build_prompt", {"error": "x went wrong"})[1] == {"error": "x went wrong"})

    chart_path = Path(tmp) / "get_chart.py"
    chart_path.write_text(chart_path.read_text().replace('"_count": "100"', '"_count": "5"'))
    fhir.seen.clear(); post("get_chart", ask)
    check("changing a number in the file changes the search on the next request", any("_count=5" in p and "category=laboratory" in p for p in fhir.seen))
    chart_path.write_text(chart_path.read_text().replace('    "labs": ("Observation"', '    # "labs": ("Observation"'))
    status, chart = post("get_chart", ask)
    check("taking a line out stops that record being read", status == 200 and "labs" not in chart)
    check("and the AI then sees 'None documented.' for results",
          "== Results (latest of each test) ==\nNone documented." in post("build_prompt", chart)[1]["request"]["input"])

    status, out = post("get_chart", {**ask, "patientId": "nobody"})
    check("an unknown patient gives a message that names the problem", status == 500 and "answered 404" in out["error"] and "Patient/nobody" in out["error"])
    os.environ["HAPI_BASE"] = f"http://127.0.0.1:{free_port()}"
    status, out = post("get_chart", ask)
    check("a server that is not running gives a message that names hapi-up", status == 500 and "hapi-up" in out["error"])
    fhir.shutdown()

    srv.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        sys.exit(f"{len(failures)} check(s) failed")
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
