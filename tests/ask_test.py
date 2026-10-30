"""Tests for ehr/ask.py against a local mock of the course proxy (run: pixi run ask-test).

No internet and no token needed. The first reply is the real shape of a proxy reply (from `codex-check --raw`).
"""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ehr import ask  # noqa: E402

MSG = [{"type": "message", "content": [{"type": "output_text", "text": "Metformin 500 mg."}]}]
REAL = {   # trimmed from a real reply: no cost anywhere, billing only names the payer
    "id": "resp_x", "object": "response", "status": "completed", "billing": {"payer": "developer"},
    "model": "gpt-5.3-codex", "output": MSG, "store": True,
    "tool_usage": {"image_gen": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}, "web_search": {"num_requests": 0}},
    "usage": {"input_tokens": 161, "input_tokens_details": {"cache_write_tokens": 0, "cached_tokens": 0},
              "output_tokens": 18, "output_tokens_details": {"reasoning_tokens": 0}, "total_tokens": 179},
}

reply: dict = {}
seen: dict = {}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        data = json.dumps(reply["body"]).encode()
        self.send_response(200)
        for k, v in reply.get("headers", {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}/v1"
    os.environ["OPENAI_TOKEN"] = "gl-test"
    failures = []

    def check(label: str, ok: bool) -> None:
        print(("PASS  " if ok else "FAIL  ") + label)
        if not ok:
            failures.append(label)

    def run(body: dict, headers: dict | None = None) -> ask.AskResult:
        reply.update(body=body, headers=headers or {})
        return ask.ask_detail("c", "q", base)

    r = run(REAL)
    check("real reply: answer, model and token counts", (r.answer, r.model, r.input_tokens, r.output_tokens) == ("Metformin 500 mg.", "gpt-5.3-codex", 161, 18))
    check("real reply: cost is estimated from the price table ($0.000534)", r.cost_estimated and abs(r.cost_usd - 0.00053375) < 1e-12)
    check("request asks the proxy not to store the chart", seen["body"].get("store") is False)
    check("request sends the system message and the chart", "clinical assistant" in seen["body"]["instructions"] and "CHART:" in seen["body"]["input"])
    check("the dashboard copy leaves out the raw reply", "raw" not in r.public() and set(r.public()) >= {"answer", "model", "input_tokens", "output_tokens", "cost_usd", "cost_estimated"})
    check("ask() returns just the text", ask.ask("c", "q", base) == "Metformin 500 mg.")

    cached = run({**REAL, "usage": {"input_tokens": 1000, "output_tokens": 100, "input_tokens_details": {"cached_tokens": 800}}})
    check("cached input tokens are priced at the cached rate", abs(cached.cost_usd - (200 * 1.75 + 800 * 0.175 + 100 * 14) / 1e6) < 1e-12)
    check("a dated model id still finds its price", run({**REAL, "model": "gpt-5.3-codex-2026-02-05"}).cost_usd is not None)
    unknown = run({**REAL, "model": "mystery-1"})
    check("an unknown model has no cost", unknown.cost_usd is None and not unknown.cost_estimated)
    hdr = run(REAL, {"x-proxy-response-cost": "0.0123"})
    check("a cost header from the proxy wins over the estimate", hdr.cost_usd == 0.0123 and not hdr.cost_estimated)
    body = run({**REAL, "usage": {**REAL["usage"], "cost": 0.5}})
    check("a cost in the reply body wins over the estimate", body.cost_usd == 0.5 and not body.cost_estimated)
    nested = run({**REAL, "billing": {"payer": "developer", "cost": {"total": 0.25}}})
    check("a nested cost object is understood", nested.cost_usd == 0.25 and not nested.cost_estimated)
    chat = run({**REAL, "usage": {"prompt_tokens": 7, "completion_tokens": 3}})
    check("chat-style token names are understood", (chat.input_tokens, chat.output_tokens) == (7, 3))
    none = run({"output": MSG})
    check("a reply with no usage still gives the answer", none.answer and none.input_tokens is None and none.cost_usd is None)

    srv.shutdown()
    if failures:
        sys.exit(f"{len(failures)} check(s) failed")
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
