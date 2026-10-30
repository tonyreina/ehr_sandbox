"""FHIR Sandbox CLI (Epic, Cerner, HAPI)."""
import os
from pathlib import Path
from typing import Annotated, Optional

import typer
from dotenv import load_dotenv

load_dotenv(override=True)

app = typer.Typer(help="FHIR sandbox demos (EHR_TYPE selects the backend).")

KEYS_DIR = Path(__file__).parent / "keys"
SMART_DIR = Path(__file__).parent / "smart-app"
SMART_PORT = 8765
SMART_BASE = f"http://localhost:{SMART_PORT}"
CODE_CONSOLE = "https://code-console.cerner.com/"
CERNER_TENANT = "ec2458f2-1e24-41c8-b71b-0e701af7583d"

_ehr_override: Optional[str] = None     # set by --ehr; wins over EHR_TYPE in .env


def _ehr_type() -> str:
    return _ehr_override or os.getenv("EHR_TYPE", "epic").lower()


def _use_ehr(ehr: Optional[str]) -> None:
    """Apply --ehr for this run (validated against the registered backends)."""
    global _ehr_override
    if ehr is None:
        return
    from ehr import ClientFactory
    if ehr.lower() not in ClientFactory.available():
        raise typer.BadParameter(f"--ehr must be one of: {', '.join(ClientFactory.available())}")
    _ehr_override = ehr.lower()


EhrOption = Annotated[
    Optional[str],
    typer.Option("--ehr", help="epic, cerner or hapi (default: EHR_TYPE in .env)"),
]

PatientArg = Annotated[
    Optional[str],
    typer.Argument(help="Test patient key for the active EHR (see list-patients) or a raw FHIR id"),
]


def _client():
    from ehr import ClientFactory
    return ClientFactory.from_env(_ehr_type())


def _hapi_patients(count: int = 20) -> list[tuple[str, str]]:
    """(FHIR id, display name) for the patients on the HAPI server."""
    from ehr.hapi import HapiFhirClient
    try:
        found = HapiFhirClient.from_env().list_patients(count)
    except Exception as e:
        raise typer.BadParameter(f"Cannot list patients on the HAPI server ({e}). Start it with `pixi run hapi-up`.")
    names = lambda p: " ".join((p.get("name") or [{}])[0].get("given", [])[:1] + [(p.get("name") or [{}])[0].get("family", "")])
    return [(p["id"], names(p)) for p in found]


def _resolve(name: Optional[str], observations: bool = False) -> tuple[str, str]:
    from ehr.patients import resolve
    if name is None and _ehr_type() == "hapi":      # no fixed test patients: use the first one on the server
        found = _hapi_patients(1)
        if not found:
            raise typer.BadParameter("The HAPI server has no patients. Run `pixi run hapi-load`.")
        return found[0][1], found[0][0]
    try:
        return resolve(_ehr_type(), name, observations=observations)
    except ValueError as e:
        raise typer.BadParameter(str(e))


@app.command()
def patient(
    name: PatientArg = None,
    ehr:  EhrOption = None,
):
    """Fetch and display patient demographics."""
    _use_ehr(ehr)
    client     = _client()
    _, patient_id = _resolve(name)
    p          = client.get_patient(patient_id)
    n          = p["name"][0]

    typer.echo(f"EHR:     {client.ehr_name}")
    typer.echo(f"Patient: {n['given'][0]} {n['family']}")
    typer.echo(f"DOB:     {p['birthDate']}")
    typer.echo(f"Gender:  {p['gender']}")
    typer.echo(f"ID:      {patient_id}")


def _obs_value(o: dict) -> str:
    """Printable value of an Observation: quantity, coded or text value, or its components (e.g. BP)."""
    if q := o.get("valueQuantity"):
        return f"{q.get('value')} {q.get('unit', '')}".strip()
    if cc := o.get("valueCodeableConcept"):
        return cc.get("text") or next((c["display"] for c in cc.get("coding", []) if c.get("display")), "")
    for key in ("valueString", "valueInteger", "valueBoolean"):
        if key in o:
            return str(o[key])
    parts = [f"{c.get('code', {}).get('text', '?')} {c['valueQuantity'].get('value')}"
             for c in o.get("component", []) if c.get("valueQuantity")]
    return ", ".join(parts)


@app.command()
def observations(
    name:     PatientArg = None,
    category: Annotated[str, typer.Option(help="Observation category")] = "laboratory",
    count:    Annotated[int, typer.Option("--count", "-n", help="Max results")] = 20,
    ehr:      EhrOption = None,
):
    """Fetch and display observations for a patient."""
    _use_ehr(ehr)
    client     = _client()
    label, patient_id = _resolve(name, observations=True)
    obs        = [o for o in client.get_observations(patient_id, category=category, count=count)
                  if o.get("resourceType") == "Observation"]       # Epic adds an OperationOutcome entry

    typer.echo(f"EHR: {client.ehr_name}")
    typer.echo(f"{category.capitalize()} results for {label} ({patient_id}):\n")
    shown = 0
    for o in obs:
        code  = o.get("code", {}).get("text", "Unknown")
        date  = o.get("effectiveDateTime", "")[:10] or " " * 10
        value = _obs_value(o)
        if value:
            typer.echo(f"  {date}  {code}: {value}")
            shown += 1
    if not shown:
        typer.echo(f"  No {category} results with a value for this patient in the sandbox.")


@app.command("generate-keys")
def generate_keys(
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite existing keys without prompting")] = False,
):
    """Generate a new RSA key pair for Epic backend authentication."""
    import sys
    sys.path.insert(0, str(KEYS_DIR))
    from generate_keys import generate
    generate(force=force)


@app.command("list-patients")
def list_patients(ehr: EhrOption = None):
    """List known sandbox test patients for the active EHR."""
    _use_ehr(ehr)
    from ehr.patients import patients_for
    header = f"{'Key':<12} {'Name':<20} {'DOB':<12} {'Sex'}  {'FHIR ID'}"
    if _ehr_type() == "hapi":                       # no fixed test patients: list what the server holds
        typer.echo(f"{'FHIR ID':<40} Name")
        for pid, name in _hapi_patients():
            typer.echo(f"{pid:<40} {name}")
        return
    patients = patients_for(_ehr_type())
    if not patients:
        typer.echo(f"No known test patients for EHR_TYPE={_ehr_type()!r}.")
        return
    typer.echo(header)
    typer.echo("-" * len(header))
    for key, (pid, name, dob, sex) in patients.items():
        typer.echo(f"{key:<12} {name:<20} {dob:<12} {sex}    {pid}")


@app.command("list-ehrs")
def list_ehrs(ehr: EhrOption = None):
    """List registered EHR backends."""
    _use_ehr(ehr)
    from ehr import ClientFactory
    current = _ehr_type()
    for name in ClientFactory.available():
        marker = " ← active" if name == current else ""
        typer.echo(f"  {name}{marker}")


@app.command("hapi-up")
def hapi_up():
    """Start a local HAPI FHIR server in Docker (data persists in a Docker volume)."""
    from ehr import hapi_local
    typer.echo("Starting HAPI (first start pulls the image and takes a minute)...")
    try:
        base = hapi_local.up()
    except Exception as e:
        typer.echo(f"Could not start HAPI: {e}", err=True)
        raise typer.Exit(1)
    typer.echo(f"HAPI is ready: {base}  ({hapi_local.patient_count()} patients)")
    typer.echo("Next: pixi run hapi-load      then: pixi run smart-app --ehr hapi")


@app.command("hapi-down")
def hapi_down(
    delete_data: Annotated[bool, typer.Option("--delete-data", help="Also delete the stored patients")] = False,
):
    """Stop the local HAPI server (patients are kept unless --delete-data)."""
    from ehr import hapi_local
    hapi_local.down(delete_data)
    typer.echo("HAPI stopped" + (" and its data deleted." if delete_data else "; data kept."))


@app.command("hapi-load")
def hapi_load(
    patients: Annotated[int, typer.Option("--patients", "-p", help="Living patients to generate")] = 25,
    seed: Annotated[int, typer.Option("--seed", "-s", help="Synthea random seed (same seed, same patients)")] = 42,
    state: Annotated[str, typer.Option(help="US state to simulate")] = "Massachusetts",
    force: Annotated[bool, typer.Option("--force", help="Load even if the server already has patients")] = False,
    numbered_names: Annotated[bool, typer.Option(
        "--numbered-names/--plain-names",
        help="Synthea's own names carry random digits (Erin498); plain names are the default")] = False,
):
    """Generate Synthea patients and load them into the local HAPI server (run hapi-up first)."""
    from ehr import hapi_local
    if not hapi_local.ready():
        typer.echo("HAPI is not running. Start it with `pixi run hapi-up`.", err=True)
        raise typer.Exit(1)
    have = hapi_local.patient_count()
    if have and not force:
        typer.echo(f"The server already has {have} patients. Use --force to add more, or "
                   "`pixi run hapi-down --delete-data` to start empty.", err=True)
        raise typer.Exit(1)
    typer.echo(f"Generating {patients} Synthea patients ({state}, seed {seed}); the first run downloads Synthea (~200 MB)...")
    fhir_dir = hapi_local.generate(patients, seed, state, numbered_names)
    typer.echo("Loading into HAPI (about 4 s per patient)...")
    for i, (name, n) in enumerate(hapi_local.load(fhir_dir), 1):
        typer.echo(f"  {i:>3}  {name[:50]:<50} {n} resources")
    typer.echo(f"Done: {hapi_local.patient_count()} patients on {hapi_local.BASE}")
    typer.echo("Try: pixi run list-patients --ehr hapi      pixi run smart-app --ehr hapi")


SMART_EHRS = ("cerner",)            # EHRs with a browser SMART sign-in to register
DASHBOARD_EHRS = ("cerner", "epic", "hapi")

# What to enter when registering the app with each EHR.
SMART_REGISTRATION = {
    "cerner": {
        "console": CODE_CONSOLE,
        "steps": "In code Console (sign in or create a CernerCare account) create a new application:",
        "rows": [
            ("Application Type",     "Provider"),
            ("Type of Access",       "Online"),
            ("Application Privacy",  "Public"),
            ("SMART Version",        "SMART v1"),
            ("Default FHIR Version", "R4"),
            ("Redirect URI",         f"{SMART_BASE}/index.html"),
            ("SMART Launch URI",     f"{SMART_BASE}/launch.html"),
            ("Scopes",               "launch, online_access, openid, fhirUser,"),
            ("",                     "user/Patient.read, user/Observation.read,"),
            ("",                     "user/MedicationRequest.read, user/AllergyIntolerance.read,"),
            ("",                     "user/Encounter.read, user/Condition.read"),
        ],
        "id_name": "Client ID",
    },
}

EPIC_NOTE = (
    "Epic needs no extra registration for the dashboard: `pixi run smart-app` signs in with your\n"
    "existing Backend Systems app (EPIC_* in .env and keys/private_key.pem) and passes the\n"
    "dashboard's read requests through on localhost. Set that up as in docs/setup/epic-portal.md."
)


def _epic_backend_ready() -> bool:
    """True when .env and keys/ have what EpicClient needs."""
    load_dotenv(override=True)
    return (all(os.getenv(k) for k in ("EPIC_CLIENT_ID", "EPIC_FHIR_BASE", "EPIC_TOKEN_URL"))
            and (KEYS_DIR / "private_key.pem").exists() and (KEYS_DIR / "public_jwks.json").exists())


def _read_smart_local() -> dict:
    """Parse smart-app/config.local.js (new JSON form, or the older single-client-id form)."""
    import json
    import re
    path = SMART_DIR / "config.local.js"
    if not path.exists():
        return {"clientIds": {}}
    text = path.read_text()
    m = re.search(r"window\.SMART_LOCAL\s*=\s*(\{.*\})\s*;", text, re.S)
    if m:
        data = json.loads(m.group(1))
        data.setdefault("clientIds", {})
        return data
    legacy = re.search(r'clientId:\s*"([^"]+)"', text)
    return {"clientIds": {"cerner": legacy.group(1)} if legacy else {}}


def _write_smart_local(data: dict) -> None:
    import json
    (SMART_DIR / "config.local.js").write_text(
        "// Generated by `pixi run smart-setup` — gitignored. Holds your per-EHR client ids\n"
        "// (identifiers, not secrets).\n"
        f"window.SMART_LOCAL = {json.dumps(data, indent=2)};\n"
    )


def _default_smart_ehr() -> str:
    env = _ehr_type()
    return env if env in DASHBOARD_EHRS else "cerner"


@app.command("smart-setup")
def smart_setup(
    ehr: Annotated[Optional[str], typer.Option("--ehr", help="cerner (epic needs no registration)")] = None,
    client_id: Annotated[Optional[str], typer.Option("--client-id", help="Client ID from the EHR's developer portal")] = None,
    open_browser: Annotated[bool, typer.Option("--open/--no-open", help="Open the developer portal in your browser")] = True,
):
    """OPTIONAL: set up a signed-in Cerner SMART session (the dashboard works without it).

    Registration itself is manual (Oracle offers no API for it and it needs your
    CernerCare login); this prints the exact values to enter, then saves the
    client ID you get back. Epic needs no registration here (see EPIC_NOTE).
    """
    import re
    import webbrowser
    import requests

    ehr = (ehr or "cerner").lower()
    if ehr == "epic":
        typer.echo(EPIC_NOTE)
        typer.echo("Backend app configured: " + ("yes" if _epic_backend_ready() else "no"))
        return
    if ehr not in SMART_REGISTRATION:
        raise typer.BadParameter(f"--ehr must be one of: {', '.join(SMART_EHRS)}")
    reg = SMART_REGISTRATION[ehr]

    typer.echo(f"1. {reg['steps']}\n")
    for k, v in reg["rows"]:
        typer.echo(f"   {k:<22} {v}")
    typer.echo(f"\n   Portal: {reg['console']}")
    if open_browser:
        webbrowser.open(reg["console"])

    typer.echo(f"\n2. After saving, copy the {reg['id_name']} from the app's details page.\n")
    if client_id is None:
        client_id = typer.prompt(reg["id_name"]).strip()
    if not re.fullmatch(r"[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", client_id):
        raise typer.BadParameter("Client ID should look like 00000000-0000-0000-0000-000000000000")

    data = _read_smart_local()
    data["clientIds"][ehr] = client_id
    _write_smart_local(data)
    typer.echo(f"Wrote {SMART_DIR / 'config.local.js'} (clients: {', '.join(data['clientIds'])})")

    url = f"https://fhir-ehr-code.cerner.com/r4/{CERNER_TENANT}/.well-known/smart-configuration"
    try:
        requests.get(url, timeout=10).raise_for_status()
        typer.echo("Sandbox reachable.")
    except requests.RequestException as e:
        typer.echo(f"Warning: could not reach {url}: {e}", err=True)

    typer.echo("\nTo load more than Patient and Observation when signed in, register those scopes and add the")
    typer.echo(f'resource names to profiles.{ehr}.resources in smart-app/config.js.')
    typer.echo(f"Next: pixi run smart-app --ehr {ehr}")


@app.command("smart-app")
def smart_app(
    ehr: Annotated[Optional[str], typer.Option("--ehr", help="cerner, epic or hapi (default: EHR_TYPE, else cerner)")] = None,
    open_browser: Annotated[bool, typer.Option("--open/--no-open", help="Open the dashboard in your browser")] = True,
    console: Annotated[bool, typer.Option("--console", help="Also open the EHR's developer portal")] = False,
    keep_hapi: Annotated[bool, typer.Option("--keep-hapi", help="With --ehr hapi: leave the local HAPI server running on exit")] = False,
):
    """Serve the patient dashboard on localhost.

    Cerner and HAPI work immediately with no login. Epic works through a local,
    read-only proxy that signs in with your Backend Systems app (.env + keys/).
    The page also has an EHR dropdown, so --ehr only sets the starting point.

    With --ehr hapi the local HAPI server (`hapi-up`) is started if it is not running and
    stopped again on Ctrl-C (patients are kept); --keep-hapi leaves it running.
    """
    import functools
    import webbrowser
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    ehr = (ehr or _default_smart_ehr()).lower()
    if ehr not in DASHBOARD_EHRS:
        raise typer.BadParameter(f"--ehr must be one of: {', '.join(DASHBOARD_EHRS)}")

    import json
    import threading

    from ehr import hapi_local
    hapi_started = False                # True when this run started the local HAPI container
    if ehr == "hapi" and not os.getenv("HAPI_FHIR_BASE") and not hapi_local.ready():
        typer.echo("Starting the local HAPI server (first start pulls the image)...")
        try:
            hapi_local.up()
            hapi_started = True
            if not hapi_local.patient_count():
                typer.echo("The local HAPI server is empty. Run `pixi run hapi-load` to add Synthea patients.")
        except Exception as e:
            typer.echo(f"Could not start the local HAPI server ({e}); the dashboard will use the public HAPI server.", err=True)

    epic_ready = _epic_backend_ready()
    # The dashboard's HAPI profile uses HAPI_FHIR_BASE from .env, else the local server when it is
    # running (`pixi run hapi-up`), else the public hapi.fhir.org test server.
    from ehr import hapi_local
    hapi_base = os.getenv("HAPI_FHIR_BASE") or (hapi_local.BASE if hapi_local.ready() else None)
    bases = {"hapi": hapi_base} if hapi_base else {}
    epic_client = None
    epic_lock = threading.Lock()

    def epic():
        nonlocal epic_client
        with epic_lock:
            if epic_client is None:
                from ehr.epic import EpicClient
                epic_client = EpicClient.from_env()
            return epic_client

    class Handler(SimpleHTTPRequestHandler):
        def _send(self, status: int, body: bytes, ctype: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _outcome(self, status: int, message: str) -> None:
            body = {"resourceType": "OperationOutcome",
                    "issue": [{"severity": "error", "code": "exception", "diagnostics": message}]}
            self._send(status, json.dumps(body).encode(), "application/fhir+json")

        def do_GET(self):
            path = self.path.split("?")[0]
            # Tells the page which EHR to start with and which proxies exist (static servers 404 this).
            if path == "/__ehr.js":
                js = (f'window.SMART_DEFAULT_EHR = "{ehr}";\n'
                      f"window.SMART_PROXY = {json.dumps({'epic': epic_ready})};\n"
                      f"window.SMART_BASES = {json.dumps(bases)};\n")
                return self._send(200, js.encode(), "text/javascript")
            # Read-only pass-through to Epic, authenticated server-side with the backend app.
            # The private key and the token never reach the browser.
            if self.path.startswith("/proxy/epic/"):
                if not epic_ready:
                    return self._outcome(503, "Epic backend app not configured (EPIC_* in .env, keys/).")
                try:
                    r = epic().get_raw(self.path[len("/proxy/epic/"):])
                except ValueError as e:
                    return self._outcome(400, str(e))
                except Exception as e:      # token or network failure
                    return self._outcome(502, f"Epic request failed: {e}")
                return self._send(r.status_code, r.content, r.headers.get("Content-Type", "application/fhir+json"))
            super().do_GET()

    try:
        server = ThreadingHTTPServer(("127.0.0.1", SMART_PORT), functools.partial(Handler, directory=str(SMART_DIR)))
    except OSError as e:
        typer.echo(f"Cannot listen on port {SMART_PORT}: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Dashboard: {SMART_BASE}/index.html  (EHR: {ehr}; Ctrl-C to stop)")
    have = _read_smart_local()["clientIds"]
    typer.echo("Epic: " + ("via local proxy using your backend app" if epic_ready
               else "not configured (set EPIC_* in .env and run generate-keys; see docs/setup/epic-portal.md)"))
    if ehr == "cerner":
        typer.echo("Signed-in SMART mode: " + ("code Console -> your app -> Test Sandbox -> Launch"
                   if "cerner" in have else "optional; run `pixi run smart-setup` to enable it"))
    if open_browser:
        webbrowser.open(f"{SMART_BASE}/index.html")
    if console and ehr in SMART_REGISTRATION:
        webbrowser.open(SMART_REGISTRATION[ehr]["console"])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        typer.echo("\nStopped.")
    finally:
        # --ehr hapi owns the local server for this session: stop it (data is kept) unless asked not to.
        if ehr == "hapi" and not keep_hapi and not os.getenv("HAPI_FHIR_BASE") and (hapi_started or hapi_local.ready()):
            typer.echo("Stopping the local HAPI server (patients are kept; `pixi run hapi-up` restarts it)...")
            hapi_local.down()


@app.command("codex-setup")
def codex_setup(
    key: Annotated[Optional[str], typer.Argument(help="Learner API key (prompted, hidden, if omitted)")] = None,
):
    """Point OpenAI Codex at the Great Learning proxy and store your learner key."""
    from ehr import codex
    if not key:
        key = typer.prompt("Learner API key", hide_input=True).strip()
    if not key:
        raise typer.BadParameter("API key must not be empty")
    path, backup = codex.write_config()
    where = codex.store_key(key)
    if backup:
        typer.echo(f"Existing Codex config saved to {backup}")
    typer.echo(f"Codex configured.\n  Config:   {path}\n  Proxy:    {codex.PROXY_URL}\n"
               f"  Model:    {codex.DEFAULT_MODEL}\n  Key ({codex.ENV_VAR}) stored in: {where}")
    typer.echo("\nNext: fully quit VS Code and reopen it (or open a new terminal and run `code`).")


if __name__ == "__main__":
    app()
