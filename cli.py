"""Epic FHIR Sandbox CLI."""
import json
import base64
import uuid
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

load_dotenv(override=True)

app = typer.Typer(help="FHIR sandbox demos (EHR_TYPE selects the backend).")

KEYS_DIR = Path(__file__).parent / "keys"

PATIENTS = {
    "camila":   ("erXuFYUfucBZaryVksYEcMg3", "Camila Lopez",     "1987-09-12", "F"),
    "derrick":  ("eq081-VQEgP8drUUqCWzHfw3",  "Derrick Lin",      "1973-06-03", "M"),
    "theodore": ("e63wRTbPfr1p8UW81d8Seiw3",  "Theodore Mychart", "1948-07-07", "M"),
    "linda":    ("eIXesllypH3M9tAA5WdJftQ3",  "Linda Ross",       "1969-04-27", "F"),
}


class PatientName(str, Enum):
    camila   = "camila"
    derrick  = "derrick"
    theodore = "theodore"
    linda    = "linda"


def _client():
    from ehr import ClientFactory
    return ClientFactory.from_env()


@app.command()
def patient(
    name: Annotated[PatientName, typer.Argument(help="Sandbox test patient")] = PatientName.camila,
):
    """Fetch and display patient demographics."""
    client     = _client()
    patient_id = PATIENTS[name.value][0]
    p          = client.get_patient(patient_id)
    n          = p["name"][0]

    typer.echo(f"EHR:     {client.ehr_name}")
    typer.echo(f"Patient: {n['given'][0]} {n['family']}")
    typer.echo(f"DOB:     {p['birthDate']}")
    typer.echo(f"Gender:  {p['gender']}")
    typer.echo(f"ID:      {patient_id}")


@app.command()
def observations(
    name:     Annotated[PatientName, typer.Argument(help="Sandbox test patient")] = PatientName.theodore,
    category: Annotated[str, typer.Option(help="Observation category")] = "laboratory",
    count:    Annotated[int, typer.Option("--count", "-n", help="Max results")] = 20,
):
    """Fetch and display observations for a patient."""
    client     = _client()
    patient_id = PATIENTS[name.value][0]
    obs        = client.get_observations(patient_id, category=category, count=count)

    if not obs:
        typer.echo("No observations found.")
        return

    typer.echo(f"EHR: {client.ehr_name}")
    typer.echo(f"{category.capitalize()} results for {name.value} ({patient_id}):\n")
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
    """List known Epic sandbox test patients."""
    header = f"{'Key':<12} {'Name':<20} {'DOB':<12} {'Sex'}  {'FHIR ID'}"
    typer.echo(header)
    typer.echo("-" * len(header))
    for key, (pid, name, dob, sex) in PATIENTS.items():
        typer.echo(f"{key:<12} {name:<20} {dob:<12} {sex}    {pid}")


@app.command("list-ehrs")
def list_ehrs():
    """List registered EHR backends."""
    from ehr import ClientFactory
    import os
    current = os.getenv("EHR_TYPE", "epic").lower()
    for name in ClientFactory.available():
        marker = " ← active" if name == current else ""
        typer.echo(f"  {name}{marker}")


if __name__ == "__main__":
    app()
