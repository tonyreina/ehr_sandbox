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

def _ehr_type() -> str:
    return os.getenv("EHR_TYPE", "epic").lower()


PatientArg = Annotated[
    Optional[str],
    typer.Argument(help="Test patient key for the active EHR (see list-patients) or a raw FHIR id"),
]


def _client():
    from ehr import ClientFactory
    return ClientFactory.from_env()


def _resolve(name: Optional[str], observations: bool = False) -> tuple[str, str]:
    from ehr.patients import resolve
    try:
        return resolve(_ehr_type(), name, observations=observations)
    except ValueError as e:
        raise typer.BadParameter(str(e))


@app.command()
def patient(
    name: PatientArg = None,
):
    """Fetch and display patient demographics."""
    client     = _client()
    _, patient_id = _resolve(name)
    p          = client.get_patient(patient_id)
    n          = p["name"][0]

    typer.echo(f"EHR:     {client.ehr_name}")
    typer.echo(f"Patient: {n['given'][0]} {n['family']}")
    typer.echo(f"DOB:     {p['birthDate']}")
    typer.echo(f"Gender:  {p['gender']}")
    typer.echo(f"ID:      {patient_id}")


@app.command()
def observations(
    name:     PatientArg = None,
    category: Annotated[str, typer.Option(help="Observation category")] = "laboratory",
    count:    Annotated[int, typer.Option("--count", "-n", help="Max results")] = 20,
):
    """Fetch and display observations for a patient."""
    client     = _client()
    label, patient_id = _resolve(name, observations=True)
    obs        = client.get_observations(patient_id, category=category, count=count)

    if not obs:
        typer.echo("No observations found.")
        return

    typer.echo(f"EHR: {client.ehr_name}")
    typer.echo(f"{category.capitalize()} results for {label} ({patient_id}):\n")
    for o in obs:
        code  = o.get("code", {}).get("text", "Unknown")
        date  = o.get("effectiveDateTime", "")[:10]
        value = o.get("valueQuantity")
        if value:
            typer.echo(f"  {date}  {code}: {value.get('value')} {value.get('unit', '')}")


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
def list_patients():
    """List known sandbox test patients for the active EHR."""
    from ehr.patients import patients_for
    header = f"{'Key':<12} {'Name':<20} {'DOB':<12} {'Sex'}  {'FHIR ID'}"
    patients = patients_for(_ehr_type())
    if not patients:
        typer.echo(f"No known test patients for EHR_TYPE={_ehr_type()!r}.")
        return
    typer.echo(header)
    typer.echo("-" * len(header))
    for key, (pid, name, dob, sex) in patients.items():
        typer.echo(f"{key:<12} {name:<20} {dob:<12} {sex}    {pid}")


@app.command("list-ehrs")
def list_ehrs():
    """List registered EHR backends."""
    from ehr import ClientFactory
    current = _ehr_type()
    for name in ClientFactory.available():
        marker = " ← active" if name == current else ""
        typer.echo(f"  {name}{marker}")


SMART_EHRS = ("cerner", "epic")      # profiles that have a sign-in (hapi has none)

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
    "epic": {
        "console": "https://fhir.epic.com/Developer/Apps",
        "steps": "At fhir.epic.com (Build Apps -> Create) register a patient-facing app (names may vary):",
        "rows": [
            ("Application Audience",  "Patients"),
            ("SMART on FHIR Version", "R4"),
            ("Confidential client",   "No (public client, PKCE)"),
            ("Redirect URI",          f"{SMART_BASE}/index.html"),
            ("Incoming APIs",         "Patient.Read (Demographics) R4,"),
            ("",                      "Observation.Read and Observation.Search (Labs, Vitals) R4"),
        ],
        "id_name": "Non-Production Client ID",
    },
}


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
    return env if env in (*SMART_EHRS, "hapi") else "cerner"


@app.command("smart-setup")
def smart_setup(
    ehr: Annotated[Optional[str], typer.Option("--ehr", help="cerner or epic (default: EHR_TYPE)")] = None,
    client_id: Annotated[Optional[str], typer.Option("--client-id", help="Client ID from the EHR's developer portal")] = None,
    open_browser: Annotated[bool, typer.Option("--open/--no-open", help="Open the developer portal in your browser")] = True,
):
    """OPTIONAL: set up a signed-in SMART session (Cerner works without it; Epic needs it).

    Registration itself is manual (no EHR offers an API for it and it needs your
    login there); this prints the exact values to enter, then saves the client ID
    you get back. Run it once per EHR.
    """
    import re
    import webbrowser
    import requests

    ehr = (ehr or _default_smart_ehr()).lower()
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

    if ehr == "cerner":
        url = f"https://fhir-ehr-code.cerner.com/r4/{CERNER_TENANT}/.well-known/smart-configuration"
    else:
        url = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/.well-known/smart-configuration"
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
):
    """Serve the patient dashboard on localhost.

    Cerner and HAPI work immediately with no login. Epic needs a registered app
    (`smart-setup --ehr epic`); the dashboard then starts the sign-in itself.
    The page also has an EHR dropdown, so --ehr only sets the starting point.
    """
    import functools
    import webbrowser
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    ehr = (ehr or _default_smart_ehr()).lower()
    if ehr not in (*SMART_EHRS, "hapi"):
        raise typer.BadParameter("--ehr must be one of: cerner, epic, hapi")

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            # Tells the page which EHR profile to start with (static servers just 404 this file).
            if self.path.split("?")[0] == "/__ehr.js":
                body = f'window.SMART_DEFAULT_EHR = "{ehr}";\n'.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/javascript")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

    try:
        server = ThreadingHTTPServer(("127.0.0.1", SMART_PORT), functools.partial(Handler, directory=str(SMART_DIR)))
    except OSError as e:
        typer.echo(f"Cannot listen on port {SMART_PORT}: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Dashboard: {SMART_BASE}/index.html  (EHR: {ehr}; Ctrl-C to stop)")
    have = _read_smart_local()["clientIds"]
    if ehr == "epic" and "epic" not in have:
        typer.echo("Epic needs a registered app: run `pixi run smart-setup --ehr epic`", err=True)
    elif ehr == "cerner":
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


if __name__ == "__main__":
    app()
