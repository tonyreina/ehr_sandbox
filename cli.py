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


@app.command("smart-setup")
def smart_setup(
    client_id: Annotated[Optional[str], typer.Option("--client-id", help="Client ID from code Console")] = None,
    open_browser: Annotated[bool, typer.Option("--open/--no-open", help="Open code Console in your browser")] = True,
):
    """OPTIONAL: set up a signed-in SMART session (the dashboard works without it).

    Registration itself is manual (Oracle has no API for it and it needs your
    CernerCare login); this prints the exact values to enter, then saves the
    client ID you get back.
    """
    import re
    import webbrowser
    import requests

    typer.echo("1. In code Console (sign in or create a CernerCare account) click New Application")
    typer.echo("   and enter exactly these values:\n")
    rows = [
        ("Application Type",   "Provider"),
        ("Type of Access",     "Online"),
        ("Application Privacy", "Public"),
        ("SMART Version",      "SMART v1"),
        ("Default FHIR Version", "R4"),
        ("Redirect URI",       f"{SMART_BASE}/index.html"),
        ("SMART Launch URI",   f"{SMART_BASE}/launch.html"),
        ("Scopes",             "launch, online_access, openid, fhirUser,"),
        ("",                   "user/Patient.read, user/Observation.read,"),
        ("",                   "user/MedicationRequest.read, user/AllergyIntolerance.read,"),
        ("",                   "user/Encounter.read, user/Condition.read"),
    ]
    for k, v in rows:
        typer.echo(f"   {k:<22} {v}")
    typer.echo(f"\n   Console: {CODE_CONSOLE}")
    if open_browser:
        webbrowser.open(CODE_CONSOLE)

    typer.echo("\n2. After saving, copy the Client ID from the Application Details page.\n")
    if client_id is None:
        client_id = typer.prompt("Client ID").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", client_id):
        raise typer.BadParameter("Client ID should look like 00000000-0000-0000-0000-000000000000")

    (SMART_DIR / "config.local.js").write_text(
        "// Generated by `pixi run smart-setup` — gitignored. Holds your code Console client id\n"
        "// (an identifier, not a secret).\n"
        f'Object.assign(window.SMART_CONFIG, {{ clientId: "{client_id}" }});\n'
    )
    typer.echo(f"Wrote {SMART_DIR / 'config.local.js'}")

    url = f"https://fhir-ehr-code.cerner.com/r4/{CERNER_TENANT}/.well-known/smart-configuration"
    try:
        requests.get(url, timeout=10).raise_for_status()
        typer.echo("Oracle Health R4 sandbox reachable.")
    except requests.RequestException as e:
        typer.echo(f"Warning: could not reach {url}: {e}", err=True)

    typer.echo("\nTo request the extra resources when signing in, add them to smartResources in")
    typer.echo('smart-app/config.js, e.g. ["Patient", "Observation", "MedicationRequest", ...].')
    typer.echo("Next: pixi run smart-app")


@app.command("smart-app")
def smart_app(
    open_browser: Annotated[bool, typer.Option("--open/--no-open", help="Open the dashboard in your browser")] = True,
    console: Annotated[bool, typer.Option("--console", help="Also open code Console (for a signed-in SMART launch)")] = False,
):
    """Serve the patient dashboard on localhost.

    Works immediately against the open Oracle Health sandbox (no login). If you
    ran `smart-setup`, launching from code Console gives a signed-in SMART session.
    """
    import functools
    import webbrowser
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(SMART_DIR))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", SMART_PORT), handler)
    except OSError as e:
        typer.echo(f"Cannot listen on port {SMART_PORT}: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Dashboard: {SMART_BASE}/index.html  (Ctrl-C to stop)")
    if (SMART_DIR / "config.local.js").exists():
        typer.echo("Signed-in SMART mode: code Console -> your app -> Test Sandbox -> pick a patient -> Launch")
    else:
        typer.echo("Signed-in SMART mode is optional; run `pixi run smart-setup` to enable it.")
    if open_browser:
        webbrowser.open(f"{SMART_BASE}/index.html")
    if console:
        webbrowser.open(CODE_CONSOLE)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        typer.echo("\nStopped.")


if __name__ == "__main__":
    app()
