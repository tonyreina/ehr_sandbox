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
shutil.copy(ROOT / "n8n" / "steps" / "pick_letter.py", tmp)
os.environ["STEPS_DIR"] = tmp
sys.path.insert(0, str(ROOT / "n8n"))
import step_server  # noqa: E402

REPLY = {"model": "gpt-5.3-codex",
         "output": [{"type": "reasoning", "content": []},
                    {"type": "message", "content": [{"type": "output_text", "text": "  Dear Colleague, "}, {"type": "output_text", "text": "Thanks.\n"}]}],
         "usage": {"input_tokens": 161, "output_tokens": 18, "input_tokens_details": {"cached_tokens": 5}}}


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

    srv.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        sys.exit(f"{len(failures)} check(s) failed")
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
