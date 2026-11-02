"""A tiny Python step server for n8n workflows. It runs in its own Docker container (ehr-steps).

POST /<name> with a JSON body runs run(body) from n8n/steps/<name>.py and sends the result back as JSON.
The file is read again on every call, so a change saved in VS Code applies to the next request.
Python only: no packages to install.
"""
import json
import os
import re
import runpy
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STEPS = os.environ.get("STEPS_DIR", "/steps")
PORT = int(os.environ.get("PORT", "8000"))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200 if self.path == "/healthz" else 404, {"ok": self.path == "/healthz"})

    def do_POST(self):
        name = self.path.strip("/")
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,40}", name):
            return self._send(400, {"error": "A step name uses lowercase letters, digits and underscores."})
        path = os.path.join(STEPS, name + ".py")
        if not os.path.isfile(path):
            return self._send(404, {"error": f"There is no step called {name}. Create n8n/steps/{name}.py."})
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"null")
            result = runpy.run_path(path)["run"](data)
            body = json.dumps(result)                    # fail here, not halfway through the reply
        except Exception as e:                           # a typo in a learner's file lands here
            print(traceback.format_exc(), flush=True)
            return self._send(500, {"error": f"{type(e).__name__}: {e}"})
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
