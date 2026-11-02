"""A small fake FHIR server for tests: read-only, built from the teaching patients in ehr/scenarios.py.

Used by the browser test and the Python-step tests, so neither needs Docker or the internet.
`server.seen` lists every request path it received.
"""
import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


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
            server.seen.append(self.path)
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

    server = ThreadingHTTPServer(("127.0.0.1", free_port()), H)
    server.seen = []
    return server
