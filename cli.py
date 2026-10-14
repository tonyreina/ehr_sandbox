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

app = typer.Typer(help="Epic FHIR sandbox demos.")

KEYS_DIR = Path(__file__).parent / "keys"

PATIENTS = {
    "camila":   ("erXuFYUfucBZaryVksYEcMg3", "Camila Lopez",    "1987-09-12", "F"),
    "derrick":  ("eq081-VQEgP8drUUqCWzHfw3",  "Derrick Lin",     "1973-06-03", "M"),
    "theodore": ("e63wRTbPfr1p8UW81d8Seiw3",  "Theodore Mychart","1948-07-07", "M"),
    "linda":    ("eIXesllypH3M9tAA5WdJftQ3",  "Linda Ross",      "1969-04-27", "F"),
}


class PatientName(str, Enum):
    camila   = "camila"
    derrick  = "derrick"
    theodore = "theodore"
    linda    = "linda"


def _fhir_base() -> str:
    import os
    base = os.getenv("EPIC_FHIR_BASE")
    if not base:
        typer.echo("EPIC_FHIR_BASE not set in .env", err=True)
        raise typer.Exit(1)
    return base


@app.command()
def patient(
    name: Annotated[PatientName, typer.Argument(help="Sandbox test patient")] = PatientName.camila,
):
    """Fetch and display patient demographics."""
    from epic_auth import authed_session

    patient_id, full_name, dob, gender = PATIENTS[name.value]
    session = authed_session()
    r = session.get(f"{_fhir_base()}/Patient/{patient_id}")
    r.raise_for_status()

    p    = r.json()
    n    = p["name"][0]
    given  = n["given"][0]
    family = n["family"]

    typer.echo(f"Patient: {given} {family}")
    typer.echo(f"DOB:     {p['birthDate']}")
    typer.echo(f"Gender:  {p['gender']}")
    typer.echo(f"ID:      {patient_id}")


@app.command()
def observations(
    name: Annotated[PatientName, typer.Argument(help="Sandbox test patient")] = PatientName.theodore,
    category: Annotated[str, typer.Option(help="Observation category")] = "laboratory",
    count: Annotated[int, typer.Option("--count", "-n", help="Max results")] = 20,
):
    """Fetch and display observations for a patient."""
    from epic_auth import authed_session

    patient_id = PATIENTS[name.value][0]
    session = authed_session()
    r = session.get(f"{_fhir_base()}/Observation", params={
        "patient":  patient_id,
        "category": category,
        "_sort":    "-date",
        "_count":   str(count),
    })
    r.raise_for_status()

    entries = r.json().get("entry", [])
    if not entries:
        typer.echo("No observations found.")
        return

    typer.echo(f"{category.capitalize()} results for {name.value} ({patient_id}):\n")
    for entry in entries:
        obs   = entry["resource"]
        code  = obs.get("code", {}).get("text", "Unknown")
        date  = obs.get("effectiveDateTime", "")[:10]
        value = obs.get("valueQuantity")
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


if __name__ == "__main__":
    app()
